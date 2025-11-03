import logging
from datetime import datetime

from models.event import Event
from repository import session

from . import batschkapp, festhalle, jahrhunderthalle, schlachthof
from .dto import EventDTO

logger = logging.getLogger(__name__)


def _load_all_events():
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


def _update_event(event_dto: EventDTO, event: Event):
    # TODO: only change update_time if any value is different and send message for interested users
    event.source = event_dto.source
    event.band = event_dto.band
    event.city = event_dto.city
    event.location = event_dto.location
    event.event_date = event_dto.date
    event.admission = event_dto.admission
    event.beginn = event_dto.beginn
    event.hint = event_dto.hint
    event.subtitle = event_dto.subtitle
    event.status = event_dto.status
    event.update_time = datetime.now()
    return event


def _insert_or_update_event(event_dto: EventDTO):
    event = session.get(Event, event_dto.id)
    if event is None:
        return _insert_event(event_dto)
    else:
        return _update_event(event_dto, event)


def load_and_persist_events():
    event_dtos = _load_all_events()
    events = [_insert_or_update_event(event_dto) for event_dto in event_dtos]
    session.commit()
    return events
