import logging
import os

import telebot

# Placeholder tokens make the package importable in environments without a
# ``.env`` (e.g. during tests or local development). The placeholder is never
# used for real API calls; production always sets real tokens via ``.env``.
TOKEN = os.getenv("TOKEN") or "000000000:TEST_TOKEN_PLACEHOLDER"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN") or "000000000:TEST_TOKEN_PLACEHOLDER"
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID") or "0"

telegram_bot = telebot.TeleBot(TOKEN)
admin_bot = telebot.TeleBot(ADMIN_TOKEN)

logger = logging.getLogger(__name__)


class _ExceptionHandler(telebot.ExceptionHandler):
    """Log unhandled update errors and reset the thread-scoped DB session.

    Returning ``True`` marks the error as handled, so a single failing update no
    longer stops polling. The session reset is a safety net for any code path
    that is not wrapped by ``with_db_session``.
    """

    def handle(self, exception):  # pragma: no cover - DB session reset + logging
        logger.exception("Unhandled error while processing a Telegram update")
        try:
            from repository import session

            session.rollback()
            remove = getattr(session, "remove", None)
            if remove is not None:
                remove()
        except Exception:
            logger.exception("Failed to reset the database session after an error")
        return True


telegram_bot.exception_handler = _ExceptionHandler()

from . import message_handler, callback_query_handler, poll_answer_handler
