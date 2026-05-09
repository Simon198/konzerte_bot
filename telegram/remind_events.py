import logging
from datetime import date, timedelta

from sqlalchemy import and_, select

from models.event import Event
from models.user import Interest, User
from repository import session

from . import telegram_bot

logger = logging.getLogger(__name__)


def _load_reminder_dates(user: User, event_date: date = date.today()):
    stmt = (
        select(Event)
        .join(Interest, Interest.event_id == Event.id)
        .where(and_(Interest.user == user, Event.event_date == event_date))
    )
    return session.scalars(stmt)


def _remind_events_today(user: User):
    for event in _load_reminder_dates(user, event_date=date.today()):
        telegram_bot.send_message(
            chat_id=user.chat_id,
            text=f"ERINNERUNG: Heute tritt auf\n{event.get_short_message_text()}",
        )


def _remind_events_in_a_week(user: User):
    for event in _load_reminder_dates(
        user, event_date=date.today() + timedelta(weeks=1)
    ):
        telegram_bot.send_message(
            chat_id=user.chat_id,
            text=f"In einer Woche tritt auf:\n{event.get_message_text()}\n\nFalls du noch keine Karte besitzt, nutze die Gelegenheit.",
        )


def remind_events():
    try:
        logger.info("Start reminding events")
        for user in session.scalars(select(User)):
            _remind_events_today(user)
            _remind_events_in_a_week(user)
        logger.info("Reminding events successfully completed")
    except:
        logger.exception("Reminding events failed")


if __name__ == "__main__":
    remind_events()
