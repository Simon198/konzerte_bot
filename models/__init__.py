from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from .event import Event
