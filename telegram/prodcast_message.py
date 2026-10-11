from sqlalchemy import and_, select

from models.user import User
from repository import session

from . import telegram_bot


def _load_admins(exclude_user_id: str | None):  # pragma: no cover - DB query
    return session.scalars(
        select(User).where(and_(User.is_admin, User.id != exclude_user_id))
    )


def prodcast_message_to_admins(message_text: str, exclude_user_id: str | None = None):  # pragma: no cover - DB + Telegram I/O
    for admin in _load_admins(exclude_user_id):
        telegram_bot.send_message(
            chat_id=admin.chat_id,
            text=message_text,
        )


def prodcast_message_to_all(message_text: str, parse_mode: str | None = None):  # pragma: no cover - DB + Telegram I/O
    for user in session.scalars(select(User)):
        telegram_bot.send_message(
            chat_id=user.chat_id, text=message_text, parse_mode=parse_mode
        )
