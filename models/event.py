import enum
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Enum, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class Source(enum.Enum):
    BATSCHKAPP = "Batschkapp"
    FESTHALLE = "Festhalle"
    JAHRHUNDERTHALLE = "Jahrhunderthalle"
    SCHLACHTHOF = "Schlachthof"


source_enum = Enum(Source, name="source_enum")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(), primary_key=True)
    source: Mapped[Source] = mapped_column(source_enum, nullable=False)
    band: Mapped[str] = mapped_column(String(), nullable=False)
    city: Mapped[str] = mapped_column(String(), nullable=False)
    location: Mapped[str] = mapped_column(String(), nullable=False)
    hint: Mapped[str | None] = mapped_column(String(), nullable=True)
    event_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    admission: Mapped[time | None] = mapped_column(Time(), nullable=True)
    beginn: Mapped[time | None] = mapped_column(Time(), nullable=True)
    subtitle: Mapped[str | None] = mapped_column(String(), nullable=True)
    status: Mapped[str | None] = mapped_column(String(), nullable=True)
    creation_time: Mapped[datetime] = mapped_column(DateTime(), default=datetime.now())
    update_time: Mapped[datetime] = mapped_column(DateTime(), default=datetime.now())

    interest: Mapped[list["Interest"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
    observed: Mapped[list["Observed"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )

    def get_german_date(self):
        return self.event_date.strftime("%d.%m.%Y")

    def _get_time_without_seconds(self, time_: time):
        return time_.strftime("%H:%M") + " Uhr"

    def get_admission_text(self):
        return self._get_time_without_seconds(self.admission)

    def get_beginn_text(self):
        return self._get_time_without_seconds(self.beginn)

    def get_message_text(self):
        text = f"{self.get_german_date()} - {self.band} ({self.city}-{self.location})"
        if self.subtitle:
            text += "\n" + self.subtitle
        if self.admission or self.beginn:
            parts = []
            if self.admission:
                parts.append(f"Einlass: {self.get_admission_text()}")
            if self.beginn:
                parts.append(f"Beginn: {self.get_beginn_text()}")
            text += "\n" + "; ".join(parts)
        if self.hint:
            text += "\n" + self.hint
        if self.status:
            text += "\nStatus: " + self.status
        return text
