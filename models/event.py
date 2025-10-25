from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(), primary_key=True)
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
