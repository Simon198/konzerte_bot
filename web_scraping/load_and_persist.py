import importlib
import logging
import threading
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy import func, or_, select

from models.band import Band
from models.event import Event, Source
from models.user import User
from repository import session
from telegram import telegram_bot

from .dto import EventDTO

logger = logging.getLogger(__name__)

SCRAPERS_DIR = "scrapers"
scrapers_dir = Path(__file__).parent / SCRAPERS_DIR


def _load_all_events():  # pragma: no cover - dynamic scraper import + network I/O
    start_time = time.time()

    for script in scrapers_dir.glob("*.py"):
        if script.name not in ["__init__.py"]:
            module_name = script.stem
            try:
                module = importlib.import_module(
                    package=f"{__package__}.{SCRAPERS_DIR}", name=f".{module_name}"
                )
                if hasattr(module, "load_events"):
                    logger.info(f"Scraper {module_name} begins")
                    try:
                        yield module.load_events()
                    except:
                        logger.exception(
                            f"The events of {module_name} could not be loaded"
                        )
                else:
                    raise ValueError(
                        f'The module {module_name} does not have a "load_events" function'
                    )
            except ImportError:
                raise ValueError(
                    f"The module {module_name} could not be loaded correctly"
                )

    end_time = time.time()
    logger.info(
        f"Successfully loaded all events in {((end_time - start_time)/60):.2f} minutes"
    )


def _get_or_create_band(name: str) -> Band:  # pragma: no cover - DB storage
    """Return the band named ``name``, creating it if it does not exist yet."""
    band = session.scalar(select(Band).where(Band.name == name))
    if band is None:
        band = Band(name=name)
        session.add(band)
    return band


def _event_from_dto(event_dto: EventDTO, band: Band) -> Event:
    """Map a scraped ``EventDTO`` to an ``Event`` ORM object (pure)."""
    return Event(
        dto_id=event_dto.id,
        source=event_dto.source,
        band=band,
        city=event_dto.city,
        location=event_dto.location,
        event_date=event_dto.date,
        admission=event_dto.admission,
        beginn=event_dto.beginn,
        hint=event_dto.hint,
        subtitle=event_dto.subtitle,
        status=event_dto.status,
    )


def _insert_event(event_dto: EventDTO, band: Band):  # pragma: no cover - DB storage
    event = _event_from_dto(event_dto, band)
    session.add(event)
    return event


def _update_observed_messages(event: Event, old_message_text: str):  # pragma: no cover - Telegram I/O
    """
    If the message text is updated, update all message of events that have been observed by users
    """
    new_message_text = event.get_message_text()
    if old_message_text == new_message_text:
        return

    for observed_event in event.observed:
        chat_id = observed_event.user.chat_id
        message_id = observed_event.message_id
        telegram_bot.edit_message_text(
            text=new_message_text, chat_id=chat_id, message_id=message_id
        )


TRANSLATIONS = {
    "band": "Band",
    "city": "Stadt",
    "location": "Lokation",
    "event_date": "Datum",
    "admission": "Einlass",
    "beginn": "Beginn",
    "hint": "Hinweis",
    "status": "Status",
}


def _format_change_texts(changes) -> list[str]:
    """Turn a ``{attr: (old, new)}`` diff into human-readable change lines (pure)."""
    return [
        f"{TRANSLATIONS[attr]}: {old_value} -> {new_value}"
        for attr, (old_value, new_value) in changes.items()
        if attr in TRANSLATIONS
    ]


def _format_change_message(event: Event, change_texts: list[str]) -> str:
    """Build the message that summarises the changes to an event (pure)."""
    return (
        f"Es gibt folgende Änderungen zu {event.band_name} ({event.event_date})\n"
        + "\n".join(change_texts)
    )


def _send_message_to_interested_users(event, changes):  # pragma: no cover - Telegram I/O
    """
    Send a message to all interested users of the changed events
    """
    change_texts = _format_change_texts(changes)
    if len(change_texts) == 0:
        return

    text = _format_change_message(event, change_texts)
    for interest in event.interest:
        telegram_bot.send_message(chat_id=interest.user.chat_id, text=text)


def _diff_event(event_dto: EventDTO, event: Event) -> dict:
    """Return ``{attr: (old_value, new_value)}`` for every changed field (pure)."""
    changes: dict[str, any] = {}
    fields = {
        "source": event_dto.source,
        "city": event_dto.city,
        "location": event_dto.location,
        "event_date": event_dto.date,
        "admission": event_dto.admission,
        "beginn": event_dto.beginn,
        "hint": event_dto.hint,
        "subtitle": event_dto.subtitle,
        "status": event_dto.status,
    }

    for attr, new_value in fields.items():
        old_value = getattr(event, attr)
        if old_value != new_value:
            changes[attr] = (old_value, new_value)

    # The band is a related object, so it is compared by name.
    old_band_name = event.band.name if event.band is not None else None
    if old_band_name != event_dto.band:
        changes["band"] = (old_band_name, event_dto.band)
    return changes


def _update_event(event_dto: EventDTO, event: Event, band: Band):  # pragma: no cover - DB + Telegram I/O
    """
    Update the DB event by the new dto object. If changes have occured, message the users
    """
    old_message_text = event.get_message_text()

    changes = _diff_event(event_dto, event)

    if len(changes) == 0:
        return event

    for attr, (_, new_value) in changes.items():
        if attr == "band":
            event.band = band
        else:
            setattr(event, attr, new_value)
    event.update_time = datetime.now()
    _update_observed_messages(event, old_message_text)
    _send_message_to_interested_users(event, changes)
    return event


def _insert_or_update_event(event_dto: EventDTO):  # pragma: no cover - DB storage
    event = session.scalar(select(Event).where(Event.dto_id == event_dto.id))
    band = _get_or_create_band(event_dto.band)
    if event is None:
        return _insert_event(event_dto, band)
    else:
        return _update_event(event_dto, event, band)


def load_and_persist_events():  # pragma: no cover - orchestration + DB + Telegram I/O
    try:
        logger.info("Start webscraping events")
        new_events: dict[Source, int] = {}
        for event_dtos in _load_all_events():
            for event_dto in event_dtos:
                if event_dto.date is None:
                    continue

                event = _insert_or_update_event(event_dto)
                if event.id is None:
                    if event.source not in new_events:
                        new_events[event.source] = 0
                    new_events[event.source] += 1
        session.flush()
        # Delete past events via the ORM so the cascade configured on
        # Event.interest / Event.observed removes the dependent rows automatically.
        past_events = session.scalars(
            select(Event).where(or_(Event.event_date.is_(None), Event.event_date < func.current_date()))
        ).all()
        for event in past_events:
            session.delete(event)
        session.commit()
        logger.info("Events have been successfully stored")

        users = session.scalars(select(User))
        for user in users:
            new_events_for_user = 0
            for source, count in new_events.items():
                if source not in (us.source for us in user.source_unsubscriptions):
                    new_events_for_user += count
            if new_events_for_user == 0:
                continue
            telegram_bot.send_message(
                user.chat_id,
                f"Es gibt {new_events_for_user} neue Events",
            )
    except:
        logger.exception("An error occurred while loading the events")


def load_and_persist_events_async():  # pragma: no cover - threading
    """Start ``load_and_persist_events`` in a background daemon thread.

    Returns the thread so callers can join it if needed. Running the scraper
    off the main polling thread keeps the bot reachable while events are
    being loaded.
    """
    thread = threading.Thread(target=load_and_persist_events, daemon=True)
    thread.start()
    return thread


if __name__ == "__main__":  # pragma: no cover
    load_and_persist_events()
