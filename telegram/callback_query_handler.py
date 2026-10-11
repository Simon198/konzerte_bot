import logging
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from telebot.types import CallbackQuery

from models.event import Event
from models.user import Interest, User
from repository import session
from utils import TIMEZONE

from . import telegram_bot
from .callback_data import CallbackData
from .consent import ACCEPT, DATENSCHUTZ_VERSION, DECLINE, get_welcome_text
from .prodcast_message import prodcast_message_to_admins
from .send_events import send_events_to_user

logger = logging.getLogger(__name__)


def _parse_callback_data(data: str) -> tuple[str, str] | None:
    """Split ``"<action>;<value>"`` callback data into its two parts (pure)."""
    parts = data.split(";")
    if len(parts) != 2:
        return None
    return parts[0], parts[1]


@telegram_bot.callback_query_handler()
def handle_callback_query(callback_query: CallbackQuery):  # pragma: no cover - DB + Telegram I/O
    message = callback_query.message
    message_id = message.id
    chat_id = message.chat.id
    user_id = callback_query.from_user.id

    user = session.get(User, user_id)

    parsed = _parse_callback_data(callback_query.data)
    if parsed is None:
        logger.warning(
            f"An unknown query callback has been sent by the user: {callback_query.data}"
        )
    else:
        callback_action, callback_value = parsed
        if callback_action == CallbackData.INTERESTED.value:
            event = session.get(Event, uuid.UUID(callback_value))
            user.interest.append(Interest(event=event))

            prodcast_message_to_admins(
                f"Nutzer @{callback_query.from_user.username} ist interessiert an:\n{event.get_short_message_text()}",
                user_id,
            )
            send_events_to_user(user, limit=1)
        elif callback_action == CallbackData.NOT_INTERESTED.value:
            event = session.get(Event, uuid.UUID(callback_value))
            # ``user.interest`` holds ``Interest`` objects, not ``Event``
            # objects, so remove the matching ``Interest`` explicitly.
            for interest in user.interest:
                if interest.event_id == event.id:
                    user.interest.remove(interest)
                    break
            send_events_to_user(user, limit=1)
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
                        f"@{callback_query.from_user.username} tritt der Gang bei",
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
        else:
            logger.warning(
                f"An unknown query callback action has been sent by the user: {callback_action}"
            )

    telegram_bot.edit_message_reply_markup(
        chat_id=chat_id, message_id=message_id, reply_markup=None
    )
    session.commit()
