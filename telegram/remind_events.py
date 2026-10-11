import logging
from datetime import date, timedelta

from sqlalchemy import and_, select

from models.event import Event
from models.user import Interest, User
from repository import session

from . import telegram_bot

logger = logging.getLogger(__name__)


def _reminder_today_text(event: Event) -> str:
    """Build the reminder message for an event happening today (pure)."""
    return f"ERINNERUNG: Heute tritt auf\n{event.get_short_message_text()}"


def _reminder_week_text(event: Event) -> str:
    """Build the reminder message for an event happening in one week (pure)."""
    return (
        f"In einer Woche tritt auf:\n{event.get_message_text()}\n\n"
        "Falls du noch keine Karte besitzt, nutze die Gelegenheit."
    )


def _load_reminder_dates(user: User, event_date: date = date.today()):  # pragma: no cover - DB query
    stmt = (
        select(Event)
        .join(Interest, Interest.event_id == Event.id)
        .where(and_(Interest.user == user, Event.event_date == event_date))
    )
    return session.scalars(stmt)


def _remind_events_today(user: User):  # pragma: no cover - DB + Telegram I/O
    for event in _load_reminder_dates(user, event_date=date.today()):
        telegram_bot.send_message(
            chat_id=user.chat_id,
            text=_reminder_today_text(event),
        )


def _remind_events_in_a_week(user: User):  # pragma: no cover - DB + Telegram I/O
    for event in _load_reminder_dates(
        user, event_date=date.today() + timedelta(weeks=1)
    ):
        telegram_bot.send_message(
            chat_id=user.chat_id,
            text=_reminder_week_text(event),
        )


def remind_events():  # pragma: no cover - orchestration + DB + Telegram I/O
    try:
        logger.info("Start reminding events")
        for user in session.scalars(select(User)):
            _remind_events_today(user)
            _remind_events_in_a_week(user)
        logger.info("Reminding events successfully completed")
    except:
        logger.exception("Reminding events failed")


if __name__ == "__main__":  # pragma: no cover
    remind_events()
