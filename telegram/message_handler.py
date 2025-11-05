import telebot
from sqlalchemy import select
from telebot.types import Message

from models.event import Event, Source
from models.poll import Poll, PollOption
from models.user import Interest, User
from repository import session

from . import telegram_bot


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


COMMANDS = {"start": start, "sources": sources, "next": next_interested_events}


def execute_command(command: str, message: Message):
    func = COMMANDS.get(command)
    if func is None:
        # TODO: send exception to user
        return

    func(message)


def handle_message(message: Message):
    command = telebot.util.extract_command(getattr(message, "text", ""))
    if command is not None:
        execute_command(command, message)
    else:
        print()
