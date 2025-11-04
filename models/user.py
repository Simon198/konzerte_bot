from typing import List

from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.event import Event, Source, source_enum

from . import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer(), unique=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean(), default=False)
    source_unsubscriptions: Mapped[list["SourceUnsubscription"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    observed: Mapped[List["Observed"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    interest: Mapped[list["Interest"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Observed(Base):
    __tablename__ = "observed_events"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    user: Mapped["User"] = relationship(back_populates="observed")
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), primary_key=True)
    event: Mapped["Event"] = relationship(back_populates="observed")
    message_id: Mapped[int] = mapped_column(Integer(), nullable=False)


class Interest(Base):
    __tablename__ = "interested_events"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    user: Mapped["User"] = relationship(back_populates="interest")
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), primary_key=True)
    event: Mapped["Event"] = relationship(back_populates="interest")


class SourceUnsubscription(Base):
    __tablename__ = "source_unsubscriptions"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    source: Mapped[Source] = mapped_column(source_enum, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="source_unsubscriptions")
