import logging
import time
from datetime import datetime

from sqlalchemy import delete, func

from models.event import Event
from repository import session
from telegram import telegram_bot

from . import batschkapp, festhalle, jahrhunderthalle, schlachthof
from .dto import EventDTO

logger = logging.getLogger(__name__)


def _load_all_events():
    logger.info("Start importing events")
    start_time = time.time()
    events: list[EventDTO] = []

    try:
        events.extend(batschkapp.load_events())
    except:
        logging.exception("The events of Batschkapp could not be loaded")

    try:
        events.extend(festhalle.load_events())
    except:
        logging.exception("The events of Festhalle could not be loaded")

    try:
        events.extend(jahrhunderthalle.load_events())
    except:
        logging.exception("The events of Jahrhunderthalle could not be loaded")

    try:
        events.extend(schlachthof.load_events())
    except:
        logging.exception("The events of Schlachthof could not be loaded")

    end_time = time.time()
    logger.info(
        f"Successfully loaded {len(events)} events in {((end_time - start_time)/60):.2f} minutes"
    )
    return events


def _insert_event(event_dto: EventDTO):
    event = Event(
        id=event_dto.id,
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
    event = session.get(Event, event_dto.id)
    if event is None:
        return _insert_event(event_dto)
    else:
        return _update_event(event_dto, event)


def load_and_persist_events():
    try:
        for event_dto in _load_all_events():
            _insert_or_update_event(event_dto)
        session.flush()
        session.execute(delete(Event).where(Event.event_date < func.current_date()))
        session.commit()
        logger.info("Events have been successfully stored")
    except:
        logger.exception("An error occurred while loading the events")
