import logging
from datetime import datetime

from dotenv import load_dotenv

import web_scraping
from models import Event
from repository import session
from web_scraping.dto import EventDTO

load_dotenv()

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


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


def _update_event(event_dto: EventDTO, event: Event):
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


def _insert_or_update_event(event_dto: EventDTO):
    event = session.get(Event, event_dto.id)
    if event is None:
        _insert_event(event_dto)
    else:
        _update_event(event_dto, event)


event_dtos = web_scraping.load_all_events()
for event_dto in event_dtos:
    _insert_or_update_event(event_dto)
session.commit()

session.close()
