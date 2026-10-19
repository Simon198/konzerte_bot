import logging
from enum import Enum

from sqlalchemy import desc, select
from telebot.types import BotCommand, Message

from models.changelog import Changelog
from models.band import Band
from models.event import Event, Source
from models.poll import Poll, PollOption
from models.user import Interest, User
from repository import session
from send_changelog import read_changelog
from utils import format_user_name

from . import telegram_bot
from .command import Commands
from .consent import (get_consent_keyboard, get_consent_text,
                      get_datenschutz_keyboard, get_welcome_text)
from .mydata import send_user_data
from .send_events import send_events_to_user

logger = logging.getLogger(__name__)


def _parse_limit(text: str, command_name: str, default: int) -> int:
    """Extract the numeric argument of a command, falling back to ``default`` (pure)."""
    try:
        return int(text.split(f"/{command_name}")[1])
    except (ValueError, IndexError):
        return default


def _build_pairings_lines(rows, current_user_id: int) -> str | None:
    """
    Build the pairings message from ``(event, user_id, username)`` query rows,
    ignoring the requesting user. Returns ``None`` when there are no pairings.
    """
    other_usernames_by_event: dict = {}
    for event, user_id, username in rows:
        if user_id == current_user_id:
            continue
        other_usernames_by_event.setdefault(event.id, (event, []))
        name = format_user_name(username=username, user_id=user_id)
        other_usernames_by_event[event.id][1].append(name)

    pairings = list(other_usernames_by_event.values())
    if not pairings:
        return None

    lines = ["Konzerte, an denen Du und andere Nutzer interessiert seid:"]
    for event, usernames in pairings:
        lines.append(f"{event.get_german_date()} - {event.band_name}: {', '.join(usernames)}")
    return "\n".join(lines)


@telegram_bot.message_handler(commands=[Commands.start.name])
def start(message: Message):  # pragma: no cover - DB + Telegram I/O
    user_id = message.from_user.id
    chat_id = message.chat.id

    db_user = session.get(User, user_id)
    if db_user is None:
        db_user = User(id=user_id, chat_id=chat_id, username=message.from_user.username)
        session.add(db_user)
    else:
        db_user.chat_id = chat_id
        db_user.username = message.from_user.username
    session.commit()

    if not db_user.consent_given:
        telegram_bot.send_message(
            chat_id=chat_id,
            text=get_consent_text(),
            reply_markup=get_consent_keyboard(),
        )
        return

    text = get_welcome_text(db_user.is_admin)
    telegram_bot.send_message(chat_id=chat_id, text=text)
    send_events_to_user(db_user, 1)


@telegram_bot.message_handler(commands=[Commands.sources.name])
def sources(message: Message):  # pragma: no cover - DB + Telegram I/O
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
def next_interested_events(message: Message):  # pragma: no cover - DB + Telegram I/O
    user_id = message.from_user.id
    chat_id = message.chat.id

    limit = _parse_limit(message.text, Commands.next.name, 100)

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
def go(message: Message):  # pragma: no cover - DB + Telegram I/O
    limit = _parse_limit(message.text, Commands.go.name, 1)

    user_id = message.from_user.id
    user = session.get(User, user_id)
    if user is None:
        logger.exception(f"Der User {user_id} konnte nicht geladen werden")
        return

    send_events_to_user(user, limit)


@telegram_bot.message_handler(commands=[Commands.changelog.name])
def changelog(message: Message):  # pragma: no cover - DB + Telegram I/O
    changelog = session.scalar(
        select(Changelog).order_by(desc(Changelog.sent_date)).limit(1)
    )
    if changelog is not None:
        answer = read_changelog(changelog)
        telegram_bot.reply_to(message=message, text=answer, parse_mode="HTML")
    else:
        telegram_bot.reply_to(
            message=message, text="Es existieren noch keine Changelog-Einträge"
        )


@telegram_bot.message_handler(commands=[Commands.datenschutz.name])
def datenschutz(message: Message):  # pragma: no cover - Telegram I/O
    telegram_bot.reply_to(
        message=message,
        text="Hier findest du die Datenschutzerklärung:",
        reply_markup=get_datenschutz_keyboard(),
    )


@telegram_bot.message_handler(commands=[Commands.mydata.name])
def mydata(message: Message):  # pragma: no cover - DB + Telegram I/O
    user = session.get(User, message.from_user.id)
    if user is None:
        telegram_bot.reply_to(
            message=message,
            text="Du bist bei mir nicht registriert. Es gibt keine gespeicherten Daten.",
        )
        return
    send_user_data(user)


@telegram_bot.message_handler(commands=[Commands.pairings.name])
def pairings(message: Message):  # pragma: no cover - DB + Telegram I/O
    user = session.get(User, message.from_user.id)
    if user is None or not user.is_admin:
        logger.warning(
            f"User {message.from_user.id} tried to use /{Commands.pairings.name} without admin rights"
        )
        telegram_bot.reply_to(
            message=message, text="Du hast keine Berechtigung für diesen Befehl"
        )
        return

    admin_interested_event_ids = select(Interest.event_id).where(
        Interest.user_id == user.id
    )
    rows = session.execute(
        select(Event, User.id, User.username)
        .join(Interest, Interest.event_id == Event.id)
        .join(User, User.id == Interest.user_id)
        .join(Band, Band.id == Event.band_id)
        .where(Event.id.in_(admin_interested_event_ids))
        .order_by(Event.event_date, Band.name)
    ).all()

    message_text = _build_pairings_lines(rows, user.id)
    if message_text is None:
        telegram_bot.send_message(
            chat_id=message.chat.id,
            text="Es gibt keine Konzerte, für die sich neben Dir noch andere Nutzer interessieren",
        )
        return

    telegram_bot.send_message(chat_id=message.chat.id, text=message_text)


@telegram_bot.message_handler(commands=[Commands.delete.name])
def delete_user(message: Message):  # pragma: no cover - DB + Telegram I/O
    user_id = message.from_user.id
    user = session.get(User, user_id)
    if user is None:
        telegram_bot.send_message(
            chat_id=message.chat.id,
            text="Du bist bei mir nicht registriert. Es gibt nichts zu löschen.",
        )
        return

    # Deleting the user cascades to all related records (Interest, Observed,
    # SourceUnsubscription) via the relationships configured on User.
    session.delete(user)
    session.commit()
    logger.info(f"User {user_id} hat seine Daten gelöscht")

    telegram_bot.send_message(
        chat_id=message.chat.id,
        text="Deine Daten wurden vollständig gelöscht. Du kannst dich jederzeit mit /start erneut registrieren.",
    )


@telegram_bot.message_handler()
def false_message(message: Message):  # pragma: no cover - Telegram I/O
    message_text = getattr(message, "text", "")
    if message_text.startswith("/"):
        logger.warning(f"Unbekanntes Kommando erhalten: {message_text.split()[0]}")
    else:
        logger.warning("Eine Nachricht konnte nicht interpretiert werden")
    telegram_bot.reply_to(
        message=message,
        text="Deine Nachricht konnte nicht interpretiert werden",
    )


def setup_bot_commands():  # pragma: no cover - Telegram I/O
    bot_commands = [BotCommand(command.name, command.value) for command in Commands]
    telegram_bot.set_my_commands(bot_commands)
