import logging
import uuid

from sqlalchemy import and_, select
from telebot.types import CallbackQuery

from models.event import Event
from models.user import Interest, User
from repository import session
from .send_events import send_events_to_user
from .callback_data import CallbackData
from .prodcast_message import prodcast_message_to_admins

from . import telegram_bot

logger = logging.getLogger(__name__)


@telegram_bot.callback_query_handler()
def handle_callback_query(callback_query: CallbackQuery):
    message = callback_query.message
    message_id = message.id
    chat_id = message.chat.id
    user_id = callback_query.from_user.id

    user = session.get(User, user_id)

    callback_query_data = callback_query.data.split(";")
    if len(callback_query_data) != 2:
        logger.warning(
            f"An unknown query callback has been sent by the user: {callback_query.data}"
        )
    else:
        callback_action, callback_value = callback_query_data
        if callback_action == CallbackData.INTERESTED.value:
            event = session.get(Event, uuid.UUID(callback_value))
            user.interest.append(Interest(event=event))

            prodcast_message_to_admins(
                f"Nutzer @{callback_query.from_user.username} ist interessiert an:\n{event.get_short_message_text()}",
                user_id,
            )
            send_events_to_user(user, limit=1)
        elif callback_action == CallbackData.NOT_INTERESTED.value:
            event = session.get(Event, uuid.UUID(callback_value))
            if event in user.interest:
                user.interest.remove(event)
            send_events_to_user(user, limit=1)
        else:
            logger.warning(
                f"An unknown query callback action has been sent by the user: {callback_action}"
            )

    telegram_bot.edit_message_reply_markup(
        chat_id=chat_id, message_id=message_id, reply_markup=None
    )
    session.commit()
