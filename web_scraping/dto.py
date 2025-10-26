from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True)
class EventDTO:
    id: str
    source: str
    band: str
    city: str
    location: str
    date: date | None
    admission: time | None
    beginn: time | None
    hint: str | None = None
    subtitle: str | None = None
    status: str | None = None
