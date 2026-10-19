from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from . import band, event, poll, user, changelog
