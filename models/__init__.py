from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from . import band, event, feature, poll, user, changelog
