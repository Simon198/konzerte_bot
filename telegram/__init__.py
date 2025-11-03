import os

import telebot

TOKEN = os.getenv("TOKEN")
telegram_bot = telebot.TeleBot(TOKEN)
