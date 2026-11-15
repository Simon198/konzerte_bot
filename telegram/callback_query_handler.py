import logging
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from telebot.types import CallbackQuery

from models.event import Event
from models.genre import Genre
from models.user import GenreUnsubscription, Interest, Observed, User
from repository import session, with_db_session
from utils import TIMEZONE, format_user_name

from . import telegram_bot
from .callback_data import CallbackData
from .consent import ACCEPT, DATENSCHUTZ_VERSION, DECLINE, get_welcome_text
from .genre_filter import build_genre_keyboard
from .prodcast_message import prodcast_message_to_admins
from .send_events import _event_markup, send_events_to_user

logger = logging.getLogger(__name__)


def _parse_callback_data(data: str) -> tuple[str, str] | None:
    """Split ``"<action>;<value>"`` callback data into its two parts (pure)."""
    parts = data.split(";")
    if len(parts) != 2:
        return None
    return parts[0], parts[1]


def _parse_event_id(value: str) -> uuid.UUID | None:
    """Parse a callback's event id, tolerating stale/tampered data (pure)."""
    try:
        return uuid.UUID(value)
    except (ValueError, TypeError):
        return None


def _clear_callback_markup(chat_id: int, message_id: int) -> None:  # pragma: no cover - Telegram I/O
    """Remove the keyboard of the clicked message so it can't be clicked again."""
    telegram_bot.edit_message_reply_markup(
        chat_id=chat_id, message_id=message_id, reply_markup=None
    )


def _toggle_genre_unsubscription(user: User, genre_id: int) -> None:
    """Add or remove ``genre_id`` from the user's disliked genres (pure)."""
    for unsubscription in user.genre_unsubscriptions:
        if unsubscription.genre_id == genre_id:
            user.genre_unsubscriptions.remove(unsubscription)
            return
    user.genre_unsubscriptions.append(GenreUnsubscription(genre_id=genre_id))


def _is_latest_active_event(user_id: int, message_id: int) -> bool:  # pragma: no cover - DB query
    """Return whether ``message_id`` is the user's most recent event message."""
    latest_message_id = session.scalar(
        select(func.max(Observed.message_id)).where(Observed.user_id == user_id)
    )
    return message_id == latest_message_id


def _apply_interest(user: User, event: Event, is_interested: bool) -> None:
    """Add or remove ``event`` from the user's interests (pure)."""
    if is_interested:
        user.interest.append(Interest(event=event))
        return
    # ``user.interest`` holds ``Interest`` objects, not ``Event`` objects, so
    # remove the matching ``Interest`` explicitly.
    for interest in user.interest:
        if interest.event_id == event.id:
            user.interest.remove(interest)
            break


def _handle_interest_callback(
    callback_value: str,
    user: User | None,
    user_id: int,
    chat_id: int,
    message_id: int,
    display_name: str,
    is_interested: bool,
) -> None:  # pragma: no cover - DB + Telegram I/O
    """Handle an "Interesse" or "Kein Interesse" callback."""
    action = "Interest" if is_interested else "Not-interested"

    if user is None:
        logger.warning(f"{action} callback from unknown user {user_id}")
        telegram_bot.send_message(
            chat_id=chat_id, text="Bitte starte mich zuerst mit /start."
        )
        _clear_callback_markup(chat_id, message_id)
        return

    event_id = _parse_event_id(callback_value)
    event = session.get(Event, event_id) if event_id is not None else None
    if event is None:
        logger.warning(f"{action} callback references missing event {callback_value}")
        _clear_callback_markup(chat_id, message_id)
        return

    _apply_interest(user, event, is_interested)
    session.commit()

    if is_interested:
        prodcast_message_to_admins(
            f"{display_name} ist interessiert an:\n{event.get_short_message_text()}",
            user_id,
        )

    telegram_bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=_event_markup(event, is_interested=is_interested),
    )
    if _is_latest_active_event(user_id, message_id):
        send_events_to_user(user, limit=1)


@telegram_bot.callback_query_handler()
@with_db_session
def handle_callback_query(callback_query: CallbackQuery):  # pragma: no cover - DB + Telegram I/O
    message = callback_query.message
    message_id = message.id
    chat_id = message.chat.id
    from_user = callback_query.from_user
    user_id = from_user.id
    display_name = format_user_name(
        username=from_user.username,
        first_name=from_user.first_name,
        last_name=from_user.last_name,
        user_id=from_user.id,
    )

    user = session.get(User, user_id)

    parsed = _parse_callback_data(callback_query.data)
    if parsed is None:
        logger.warning(
            f"An unknown query callback has been sent by the user: {callback_query.data}"
        )
    else:
        callback_action, callback_value = parsed
        if callback_action == CallbackData.INTERESTED.value:
            _handle_interest_callback(
                callback_value=callback_value,
                user=user,
                user_id=user_id,
                chat_id=chat_id,
                message_id=message_id,
                display_name=display_name,
                is_interested=True,
            )
            return
        elif callback_action == CallbackData.NOT_INTERESTED.value:
            _handle_interest_callback(
                callback_value=callback_value,
                user=user,
                user_id=user_id,
                chat_id=chat_id,
                message_id=message_id,
                display_name=display_name,
                is_interested=False,
            )
            return
        elif callback_action == CallbackData.CONSENT.value:
            if callback_value == ACCEPT:
                if user is None:
                    logger.warning(f"Consent callback from unknown user {user_id}")
                    telegram_bot.send_message(
                        chat_id=chat_id, text="Bitte starte mich zuerst mit /start."
                    )
                else:
                    user.consent_given = True
                    user.consent_date = datetime.now(tz=ZoneInfo(TIMEZONE))
                    user.consent_version = DATENSCHUTZ_VERSION
                    prodcast_message_to_admins(
                        f"{display_name} tritt der Gang bei",
                        user_id,
                    )
                    text = get_welcome_text(user.is_admin)
                    telegram_bot.send_message(chat_id=chat_id, text=text)
                    send_events_to_user(user, 1)
            elif callback_value == DECLINE:
                telegram_bot.send_message(
                    chat_id=chat_id,
                    text="Ohne deine Einwilligung kann ich dir keine Nachrichten senden. "
                    "Deine Daten kannst du jederzeit mit /delete löschen.",
                )
            else:
                logger.warning(
                    f"An unknown consent callback value has been sent by the user: {callback_value}"
                )
        elif callback_action == CallbackData.GENRE.value:
            if user is None:
                logger.warning(f"Genre callback from unknown user {user_id}")
                telegram_bot.send_message(
                    chat_id=chat_id, text="Bitte starte mich zuerst mit /start."
                )
            else:
                _toggle_genre_unsubscription(user, int(callback_value))
                session.commit()
                genres = session.scalars(select(Genre).order_by(Genre.name)).all()
                disliked_ids = {u.genre_id for u in user.genre_unsubscriptions}
                telegram_bot.edit_message_reply_markup(
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=build_genre_keyboard(genres, disliked_ids),
                )
            return
        elif callback_action == CallbackData.GENRE_DONE.value:
            session.commit()
            _clear_callback_markup(chat_id, message_id)
            return
        else:
            logger.warning(
                f"An unknown query callback action has been sent by the user: {callback_action}"
            )

    _clear_callback_markup(chat_id, message_id)
    session.commit()
