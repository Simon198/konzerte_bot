from sqlalchemy import Column, ForeignKey, Integer, String, Table, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


# Association table linking bands to their genres (many-to-many).
band_genres = Table(
    "band_genres",
    Base.metadata,
    Column("band_id", UUID(), ForeignKey("bands.id"), primary_key=True),
    Column("genre_id", Integer(), ForeignKey("genres.id"), primary_key=True),
)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    name: Mapped[str] = mapped_column(String(), unique=True, nullable=False)

    bands: Mapped[list["Band"]] = relationship(
        secondary=band_genres, back_populates="genres"
    )
