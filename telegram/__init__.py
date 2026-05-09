import os

import telebot

TOKEN = os.getenv("TOKEN")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

telegram_bot = telebot.TeleBot(TOKEN)
admin_bot = telebot.TeleBot(ADMIN_TOKEN)

from . import message_handler, callback_query_handler, poll_answer_handler
