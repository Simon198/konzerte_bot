import logging
from typing import Callable, TypedDict

import telebot
from sqlalchemy import select
from telebot.types import Message

from models.event import Event, Source
from models.feature import Feature
from models.poll import Poll, PollOption
from models.user import Interest, User
from repository import session
from telegram.get_admins import send_message_to_admins

from . import telegram_bot

logger = logging.getLogger(__name__)


def start(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    db_user = session.get(User, user_id)
    if db_user is None:
        db_user = User(id=user_id, chat_id=chat_id)
        session.add(db_user)
    else:
        db_user.chat_id = chat_id

    text = "Willkommen" + (", meine Hoheit" if db_user.is_admin else "")
    telegram_bot.send_message(chat_id=chat_id, text=text)
    send_message_to_admins(f"@{message.from_user.username} tritt der Gang bei")


def sources(message: Message):
    chat_id = message.chat.id

    stmt = select(Event.source).distinct().order_by(Event.source)

    question = "Zu welchen Quellen möchtest du benachrichtigt werden?"
    options: list[str] = [source.value for source in session.scalars(stmt).all()]

    poll_response = telegram_bot.send_poll(
        chat_id=chat_id,
        question=question,
        options=options,
        is_anonymous=False,
        allows_multiple_answers=True,
    ).poll
    poll = Poll(
        id=poll_response.id,
        poll_options=[
            PollOption(id=index, source=Source(option.text))
            for index, option in enumerate(poll_response.options)
        ],
    )
    session.add(poll)


def next_interested_events(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        limit = int(message.text.split("/next")[1])
    except:
        limit = 5

    stmt = (
        select(Event)
        .distinct()
        .join(Interest, Interest.event_id == Event.id)
        .where(Interest.user_id == user_id)
        .order_by(Event.event_date.asc())
        .limit(limit)
    )
    for event in session.scalars(stmt):
        telegram_bot.send_message(chat_id=chat_id, text=event.get_message_text())


def feature(message: Message):
    user = session.get(User, message.from_user.id)

    feature_text = message.text.split("/feature")[1].strip()
    if len(feature_text) == 0:
        telegram_bot.reply_to(
            message=message, text="Gib deinen Feature-Wunsch hinter dem Befehl an"
        )
        return

    feature = Feature(user=user, text=feature_text)
    session.add(feature)
    session.commit()
    telegram_bot.reply_to(message=message, text="Dein Feature-Wunsch wurde aufgenommen")


class Command(TypedDict):
    cmd: Callable[[Message], None]
    description: str


COMMANDS: dict[str, Command] = {
    "start": {"cmd": start, "description": "Registrierung neuer Nutzer"},
    "sources": {
        "cmd": sources,
        "description": "Konfiguration, von welchen Veranstaltern Du Events erhalten möchtest",
    },
    "next": {
        "cmd": next_interested_events,
        "description": "Lädt die nächsten n Konzerte, die Dich interessieren. Wenn keine Zahl nach dem Kommando steht, werden die nächsten 5 Konzerte geladen.",
    },
    "feature": {
        "cmd": feature,
        "description": "Schreibe ein Feature-Wunsch, der dir wichtig ist",
    },
}


def execute_command(command: str, message: Message):
    func = COMMANDS.get(command)
    if func is None:
        telegram_bot.reply_to(
            message=message,
            text=f"Dein Kommando ist unbekannt. Erlaubte Kommandos:\n"
            + "\n".join(
                [f"/{key}: {value["description"]}" for key, value in COMMANDS.items()]
            ),
        )
        logger.warning(f"Unknown command from user: {command}")
        return

    logger.info(f"Executing command: /{command}")
    func["cmd"](message)


def handle_message(message: Message):
    message_text = getattr(message, "text", "")
    command = telebot.util.extract_command(message_text)
    if command is not None:
        execute_command(command, message)
    else:
        logger.warning(f"The user's message could not be interpreted: {message_text}")
        telegram_bot.reply_to(
            message=message,
            text=f"Deine Nachricht konnte nicht interpretiert werden",
        )
