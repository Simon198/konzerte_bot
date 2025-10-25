from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True)
class Event:
    id: str
    band: str
    city: str
    location: str
    hint: str
    date: date
    admission: time
    beginn: time


@dataclass(frozen=True)
class BatschkappEvent(Event):
    subtitle: str
    status: str


@dataclass(frozen=True)
class FesthalleEvent(Event):
    pass


@dataclass(frozen=True)
class JahrhunderthalleEvent(Event):
    id: str
    subtitle: str


@dataclass(frozen=True)
class SchlachthofEvent(Event):
    subtitle: str
