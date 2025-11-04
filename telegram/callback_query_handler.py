from telebot.types import CallbackQuery

from models.event import Event
from models.user import User
from repository import session

from . import telegram_bot


def handle_callback_query(callback_query: CallbackQuery):
    message = callback_query.message
    message_id = message.id
    chat_id = message.chat.id
    user_id = callback_query.from_user.id

    user = session.get(User, user_id)
    if callback_query.data.startswith("interested"):
        event_id = callback_query.data.split(";")[1]
        event = session.get(Event, event_id)
        user.interest.append(event)
    elif callback_query.data.startswith("not_interested"):
        event_id = callback_query.data.split(";")[1]
        event = session.get(Event, event_id)
        if event in user.interest:
            user.interest.remove(event)

    telegram_bot.edit_message_reply_markup(
        chat_id=chat_id, message_id=message_id, reply_markup=None
    )
    session.commit()
