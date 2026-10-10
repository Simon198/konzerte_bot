import importlib
import logging
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete, func, select

from models.event import Event, Source
from models.user import User
from repository import session
from telegram import telegram_bot

from .dto import EventDTO

logger = logging.getLogger(__name__)

SCRAPERS_DIR = "scrapers"
scrapers_dir = Path(__file__).parent / SCRAPERS_DIR


def _load_all_events():
    start_time = time.time()

    for script in scrapers_dir.glob("*.py"):
        if script.name not in ["__init__.py"]:
            module_name = script.stem
            try:
                module = importlib.import_module(
                    package=f"{__package__}.{SCRAPERS_DIR}", name=f".{module_name}"
                )
                if hasattr(module, "load_events"):
                    try:
                        yield module.load_events()
                    except:
                        logging.exception(
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


def _insert_event(event_dto: EventDTO):
    event = Event(
        dto_id=event_dto.id,
        source=event_dto.source,
        band=event_dto.band,
        city=event_dto.city,
        location=event_dto.location,
        event_date=event_dto.date,
        admission=event_dto.admission,
        beginn=event_dto.beginn,
        hint=event_dto.hint,
        subtitle=event_dto.subtitle,
        status=event_dto.status,
    )
    session.add(event)
    return event


def _update_observed_messages(event: Event, old_message_text: str):
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


def _send_message_to_interested_users(event, changes):
    """
    Send a message to all interested users of the changed events
    """
    for interest in event.interest:
        chat_id = interest.user.chat_id
        change_texts: list[str] = []
        for attr, (old_value, new_value) in changes.items():
            if attr not in TRANSLATIONS:
                continue
            change_texts.append(f"{TRANSLATIONS[attr]}: {old_value} -> {new_value}")

        if len(change_texts) == 0:
            continue

        text = (
            f"Es gibt folgende Änderungen zu {event.band} ({event.event_date})\n"
            + "\n".join(change_texts)
        )
        telegram_bot.send_message(chat_id=chat_id, text=text)


def _update_event(event_dto: EventDTO, event: Event):
    """
    Update the DB event by the new dto object. If changes have occured, message the users
    """
    old_message_text = event.get_message_text()

    changes: dict[str, any] = {}
    fields = {
        "source": event_dto.source,
        "band": event_dto.band,
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
            setattr(event, attr, new_value)
            changes[attr] = (old_value, new_value)

    if len(changes) == 0:
        return event

    event.update_time = datetime.now()
    _update_observed_messages(event, old_message_text)
    _send_message_to_interested_users(event, changes)
    return event


def _insert_or_update_event(event_dto: EventDTO):
    event = session.scalar(select(Event).where(Event.dto_id == event_dto.id))
    if event is None:
        return _insert_event(event_dto)
    else:
        return _update_event(event_dto, event)


def load_and_persist_events():
    try:
        logger.info("Start webscraping events")
        new_events: dict[Source, int] = {}
        for event_dtos in _load_all_events():
            for event_dto in event_dtos:
                event = _insert_or_update_event(event_dto)
                if event.id is None:
                    if event.source not in new_events:
                        new_events[event.source] = 0
                    new_events[event.source] += 1
        session.flush()
        session.execute(delete(Event).where(Event.event_date < func.current_date()))
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


if __name__ == "__main__":
    load_and_persist_events()
