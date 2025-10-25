from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import web_scraping
from models import Base, Event
from web_scraping.dto import EventDTO

engine = create_engine("sqlite:///concerts.db", echo=True)
Base.metadata.create_all(engine)


def _insert_event(session: Session, event_dto: EventDTO):
    event = Event(
        id=event_dto.id,
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


def _update_event(event_dto: EventDTO, event: Event):
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


def _insert_or_update_event(session: Session, event_dto: EventDTO):
    event = session.get(Event, event_dto.id)
    if event is None:
        _insert_event(session, event_dto)
    else:
        _update_event(event_dto, event)


# Create session
with Session(engine) as session:
    event_dtos = web_scraping.load_all_events()
    for event_dto in event_dtos:
        _insert_or_update_event(session, event_dto)
    session.commit()
