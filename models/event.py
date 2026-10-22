import enum
from datetime import date, datetime, time
import uuid

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Time, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from .band import Band


class Source(enum.Enum):
    BATSCHKAPP = "Batschkapp"
    FESTHALLE = "Festhalle"
    JAHRHUNDERTHALLE = "Jahrhunderthalle"
    SCHLACHTHOF = "Schlachthof"
    ZOOM = "Zoom"


source_enum = Enum(Source, name="source_enum")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    dto_id: Mapped[str] = mapped_column(String(), unique=True, nullable=False)
    source: Mapped[Source] = mapped_column(source_enum, nullable=False)
    band_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bands.id"), nullable=False)
    city: Mapped[str] = mapped_column(String(), nullable=False)
    location: Mapped[str] = mapped_column(String(), nullable=False)
    hint: Mapped[str | None] = mapped_column(String(), nullable=True)
    event_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    admission: Mapped[time | None] = mapped_column(Time(), nullable=True)
    beginn: Mapped[time | None] = mapped_column(Time(), nullable=True)
    subtitle: Mapped[str | None] = mapped_column(String(), nullable=True)
    status: Mapped[str | None] = mapped_column(String(), nullable=True)
    url: Mapped[str | None] = mapped_column(String(), nullable=True)
    creation_time: Mapped[datetime] = mapped_column(DateTime(), default=datetime.now)
    update_time: Mapped[datetime] = mapped_column(DateTime(), default=datetime.now)

    band: Mapped["Band"] = relationship(back_populates="events")

    interest: Mapped[list["Interest"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
    observed: Mapped[list["Observed"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )

    def get_german_date(self):
        if self.event_date is None:
            return "(?)"
        return self.event_date.strftime("%d.%m.%Y")

    @property
    def band_name(self) -> str | None:
        """Return the band's name, tolerating a not-yet-loaded relationship."""
        return self.band.name if self.band is not None else None

    def _get_time_without_seconds(self, time_: time):
        return time_.strftime("%H:%M") + " Uhr"

    def get_admission_text(self):
        return self._get_time_without_seconds(self.admission)

    def get_beginn_text(self):
        return self._get_time_without_seconds(self.beginn)

    def get_short_message_text(self):
        return f"{self.get_german_date()} - {self.band_name} ({self.city}-{self.location})"

    def get_genre_text(self) -> str | None:
        """Return the band's genres as a comma-separated string, or ``None``."""
        if self.band is None or not self.band.genres:
            return None
        return ", ".join(sorted(genre.name for genre in self.band.genres))

    def get_message_text(self):
        text = self.get_short_message_text()
        if self.subtitle:
            text += "\n" + self.subtitle
        genre_text = self.get_genre_text()
        if genre_text:
            text += "\nGenre: " + genre_text
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
