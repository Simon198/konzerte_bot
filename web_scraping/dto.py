from dataclasses import dataclass
from datetime import date, time

from models.event import Source


@dataclass(frozen=True)
class EventDTO:
    id: str
    source: Source
    band: str
    city: str
    location: str
    date: date | None
    admission: time | None
    beginn: time | None
    hint: str | None = None
    subtitle: str | None = None
    status: str | None = None
    url: str | None = None
