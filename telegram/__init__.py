import os

import telebot

TOKEN = os.getenv("TOKEN")
telegram_bot = telebot.TeleBot(TOKEN)

from .bot import run_telegram_bot
