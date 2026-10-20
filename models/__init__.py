from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from . import genre, band, event, poll, user, changelog
