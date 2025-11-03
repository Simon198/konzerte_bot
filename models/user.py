from typing import List

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.event import Event, Source, source_enum

from . import Base

observed_events_table = Table(
    "observed_events",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("event_id", ForeignKey("events.id"), primary_key=True),
)
interested_events_table = Table(
    "interested_events",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("event_id", ForeignKey("events.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer(), unique=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean(), default=False)
    source_unsubscriptions: Mapped[list["SourceUnsubscription"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    observed_events: Mapped[List["Event"]] = relationship(
        secondary=observed_events_table
    )
    interested_events: Mapped[list["Event"]] = relationship(
        secondary=interested_events_table
    )


class SourceUnsubscription(Base):
    __tablename__ = "source_unsubscriptions"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    source: Mapped[Source] = mapped_column(source_enum, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="source_unsubscriptions")
