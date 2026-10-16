import logging

from sqlalchemy import and_, not_, select
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from models.event import Event
from models.user import Observed, User
from repository import session

from . import telegram_bot

logger = logging.getLogger(__name__)


def _event_markup(event: Event) -> InlineKeyboardMarkup:
    """Build the interested / not-interested reply keyboard for an event (pure)."""
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Interesse", callback_data=f"interested;{event.id}"),
        InlineKeyboardButton("❌ Kein Interesse", callback_data=f"not_interested;{event.id}"),
    )
    return markup


def send_events_to_user(user: User, limit: int = 1):  # pragma: no cover - DB + Telegram I/O
    stmt = (
        select(Event)
        .where(
            and_(
                not_(
                    Event.id.in_(
                        select(Observed.event_id)
                        .distinct()
                        .where(Observed.user_id == user.id)
                    )
                ),
                not_(
                    Event.source.in_(
                        unsubscription.source
                        for unsubscription in user.source_unsubscriptions
                    )
                ),
            )
        )
        .order_by(Event.event_date.is_(None), Event.event_date, Event.beginn)
        .limit(limit)
    )

    events = session.scalars(stmt).all()
    for event in events:
        markup = _event_markup(event)

        message = telegram_bot.send_message(
            chat_id=user.chat_id, text=event.get_message_text(), reply_markup=markup
        )

        observed_event = Observed(event_id=event.id, message_id=message.id)
        user.observed.append(observed_event)
        session.commit()
