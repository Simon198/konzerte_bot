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

from . import message_handler, callback_query_handler, poll_answer_handler
