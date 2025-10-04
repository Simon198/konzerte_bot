from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Event:
    band: str
    city: str
    location: str
    hint: str
    admission: datetime
    beginn: datetime


@dataclass(frozen=True)
class BatschkappEvent(Event):
    id: str
    subtitle: str
    status: str
