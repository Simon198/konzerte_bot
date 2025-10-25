import logging
import os

import telebot
from telebot.types import Update

from models.user import User
from repository import session

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

TOKEN = os.getenv("TOKEN")
tb = telebot.TeleBot(TOKEN)


def start(update: Update):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id

    db_user = session.get(User, user_id)
    if db_user is None:
        db_user = User(id=user_id, chat_id=chat_id)
        session.add(db_user)
    else:
        db_user.chat_id = chat_id

    text = "Willkommen" + (", meine Hoheit" if db_user.is_admin else "")
    tb.send_message(chat_id=chat_id, text=text)
    # TODO: send list of all events
    # TODO: store message id to update later
    print()


def location():
    # TODO: select locations?
    print()


COMMANDS = {"start": start, "location": location}


def execute_command(command: str):
    func = COMMANDS.get(command)
    if func is None:
        # TODO: send exception to user
        return

    func(update)


offset = None
while True:
    updates = tb.get_updates(offset=offset)
    if len(updates) == 0:
        break

    for update in updates:

        command = telebot.util.extract_command(update.message.text)
        if command is not None:
            execute_command(command)
        else:
            # TODO: what to do
            print()

        session.commit()
        if offset is None or update.update_id > offset:
            offset = update.update_id
print()
