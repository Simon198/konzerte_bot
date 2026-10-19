import uuid

from sqlalchemy import String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class Band(Base):
    __tablename__ = "bands"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(), unique=True, nullable=False)
    audio_sample: Mapped[str | None] = mapped_column(String(), nullable=True)

    events: Mapped[list["Event"]] = relationship(back_populates="band")
