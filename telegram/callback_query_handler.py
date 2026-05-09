import logging

from sqlalchemy import and_, select
from telebot.types import CallbackQuery

from models.event import Event
from models.user import Interest, User
from repository import session
from telegram.send_message_to_admins import send_message_to_admins

from . import telegram_bot

logger = logging.getLogger(__name__)


@telegram_bot.callback_query_handler()
def handle_callback_query(callback_query: CallbackQuery):
    message = callback_query.message
    message_id = message.id
    chat_id = message.chat.id
    user_id = callback_query.from_user.id

    user = session.get(User, user_id)
    if callback_query.data.startswith("interested"):
        event_id = callback_query.data.split(";")[1]
        event = session.get(Event, event_id)
        user.interest.append(Interest(event=event))

        send_message_to_admins(
            f"Nutzer @{callback_query.from_user.username} ist interessiert an:\n{event.get_short_message_text()}",
            user_id,
        )
    elif callback_query.data.startswith("not_interested"):
        event_id = callback_query.data.split(";")[1]
        event = session.get(Event, event_id)
        if event in user.interest:
            user.interest.remove(event)
    else:
        logger.warning(
            f"An unknown query callback has been sent by the user: {callback_query.data}"
        )

    telegram_bot.edit_message_reply_markup(
        chat_id=chat_id, message_id=message_id, reply_markup=None
    )
    session.commit()
