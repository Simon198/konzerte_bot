from sqlalchemy import Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.event import Source

from . import Base


class Poll(Base):
    __tablename__ = "polls"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    poll_options: Mapped[list["PollOption"]] = relationship(
        back_populates="poll", cascade="all, delete-orphan"
    )


class PollOption(Base):
    __tablename__ = "poll_options"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey("polls.id"), primary_key=True)
    source: Mapped[Source] = mapped_column(Enum(Source), nullable=False)
    poll: Mapped["Poll"] = relationship(back_populates="poll_options")
