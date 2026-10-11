from datetime import datetime
import uuid
from sqlalchemy import UUID, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Changelog(Base):
    __tablename__ = "changelogs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid.uuid4
    )
    file_name: Mapped[str] = mapped_column(String(), nullable=False)
    sent_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
