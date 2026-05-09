import logging

from sqlalchemy import and_, not_, select
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from models.event import Event
from models.user import Observed, User
from repository import session

from . import telegram_bot

logger = logging.getLogger(__name__)


def send_events_to_user(user: User):
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
        .limit(5)
    )

    events = session.scalars(stmt).all()
    logger.info(f"Sending {len(events)} events to user {user.id}")
    for event in events:
        markup = InlineKeyboardMarkup()
        btn_yes = InlineKeyboardButton(
            "✅ Interesse", callback_data=f"interested;{event.id}"
        )
        btn_no = InlineKeyboardButton(
            "❌ Kein Interesse", callback_data=f"not_interested;{event.id}"
        )
        markup.add(btn_yes, btn_no)

        message = telegram_bot.send_message(
            chat_id=user.chat_id, text=event.get_message_text(), reply_markup=markup
        )

        observed_event = Observed(user=user, event_id=event.id, message_id=message.id)
        user.observed.append(observed_event)
        session.commit()


def send_events():
    try:
        logger.info("Starting sending events")
        for user in session.scalars(select(User)):
            send_events_to_user(user)
        logger.info("Events have been successfully sent")
    except:
        logger.exception("Sending events failed")


if __name__ == "__main__":
    send_events()
