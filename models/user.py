from sqlalchemy import Boolean, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.event import Source

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


class SourceUnsubscription(Base):
    __tablename__ = "source_unsubscriptions"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    source: Mapped[Source] = mapped_column(Enum(Source), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="source_unsubscriptions")
