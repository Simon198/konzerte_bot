from sqlalchemy import and_, select

from models.user import User
from repository import session

from . import telegram_bot


def _get_admins(current_user_id: str):
    return session.scalars(
        select(User).where(and_(User.is_admin, User.id != current_user_id))
    )


def send_message_to_admins(message_text: str, current_user_id: str | None = None):
    for admin in _get_admins(current_user_id):
        telegram_bot.send_message(
            chat_id=admin.chat_id,
            text=message_text,
        )
