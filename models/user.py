from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer(), unique=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean(), default=False)
