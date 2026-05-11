from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from . import event, feature, poll, user, changelog
