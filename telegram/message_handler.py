from enum import Enum
import logging

from sqlalchemy import select
from telebot.types import Message, BotCommand

from models.event import Event, Source
from models.feature import Feature
from models.poll import Poll, PollOption
from models.user import Interest, User
from repository import session
from .send_events import send_events_to_user
from .send_message_to_admins import send_message_to_admins

from . import telegram_bot

logger = logging.getLogger(__name__)


class Commands(Enum):
    start = "Registrierung neuer Nutzer"
    sources = "Konfiguration, von welchen Veranstaltern Du Events erhalten möchtest"
    go = "Lädt die nächsten n Konzerte, über die Du noch nicht informiert wurdest. Wenn keine Zahl nach dem Kommando steht, werden die nächsten 5 Konzerte geladen."
    next = "Lädt die nächsten n Konzerte, die Dich interessieren. Wenn keine Zahl nach dem Kommando steht, werden die nächsten 5 Konzerte geladen."
    feature = "Schreibe ein Feature-Wunsch, der dir wichtig ist"


@telegram_bot.message_handler(commands=[Commands.start.name])
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
    send_message_to_admins(f"@{message.from_user.username} tritt der Gang bei", user_id)
    session.commit()


@telegram_bot.message_handler(commands=[Commands.sources.name])
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
    session.commit()


@telegram_bot.message_handler(commands=[Commands.next.name])
def next_interested_events(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        limit = int(message.text.split(f"/{Commands.next.name}")[1])
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
    events = session.scalars(stmt).all()
    if len(events) == 0:
        telegram_bot.send_message(
            chat_id=chat_id,
            text="Es gibt keine anstehenden Konzerte, die dich interessieren",
        )
    else:
        for event in events:
            telegram_bot.send_message(chat_id=chat_id, text=event.get_message_text())


@telegram_bot.message_handler(commands=[Commands.go.name])
def go(message: Message):
    try:
        limit = int(message.text.split(f"/{Commands.go.name}")[1])
    except:
        limit = 5

    user_id = message.from_user.id
    user = session.get(User, user_id)
    if user is None:
        logger.exception(f"Der User {user_id} konnte nicht geladen werden")
        return

    send_events_to_user(user, limit)


@telegram_bot.message_handler(commands=[Commands.feature.name])
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


@telegram_bot.message_handler()
def false_message(message: Message):
    message_text = getattr(message, "text", "")
    logger.warning(f"The user's message could not be interpreted: {message_text}")
    telegram_bot.reply_to(
        message=message,
        text=f"Deine Nachricht konnte nicht interpretiert werden",
    )


def setup_bot_commands():
    bot_commands = [BotCommand(command.name, command.value) for command in Commands]
    telegram_bot.set_my_commands(bot_commands)
