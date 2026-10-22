import logging
import os

from sqlalchemy import and_, not_, select
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from models.event import Event
from models.genre import band_genres
from models.user import Observed, User
from repository import session

from . import telegram_bot

logger = logging.getLogger(__name__)


def _event_markup(event: Event) -> InlineKeyboardMarkup:
    """Build the interested / not-interested reply keyboard for an event (pure)."""
    markup = InlineKeyboardMarkup()

    audio_sample = event.band.audio_sample if event.band is not None else None
    if audio_sample:
        markup.add(InlineKeyboardButton("Hörprobe", url=audio_sample))

    markup.add(
        InlineKeyboardButton("✅ Interesse", callback_data=f"interested;{event.id}"),
        InlineKeyboardButton("❌ Kein Interesse", callback_data=f"not_interested;{event.id}"),
    )
    return markup


def _band_image_path(event: Event) -> str | None:
    """Return the band's stored image path if it exists on disk (pure)."""
    image_path = event.band.image_path if event.band is not None else None
    if image_path and os.path.isfile(image_path):
        return image_path
    return None


def _send_band_sticker(event: Event, chat_id: int):  # pragma: no cover - Telegram I/O
    """Send the band's image as a small sticker."""
    image_path = _band_image_path(event)
    if image_path is None:
        return
    try:
        with open(image_path, "rb") as sticker:
            telegram_bot.send_sticker(chat_id=chat_id, sticker=sticker)
    except Exception:
        logger.exception("Could not send band sticker for %r", event.band_name)


def send_events_to_user(user: User, limit: int = 1):  # pragma: no cover - DB + Telegram I/O
    conditions = [
        not_(
            Event.id.in_(
                select(Observed.event_id)
                .distinct()
                .where(Observed.user_id == user.id)
            )
        ),
        not_(
            Event.source.in_(
                unsubscription.source
                for unsubscription in user.source_unsubscriptions
            )
        ),
    ]

    # Exclude events whose band is tagged with a genre the user dislikes. Only
    # disliked genres are stored, so newly created genres are subscribed by
    # default without iterating over every user.
    disliked_genre_ids = [u.genre_id for u in user.genre_unsubscriptions]
    if disliked_genre_ids:
        conditions.append(
            not_(
                Event.id.in_(
                    select(Event.id)
                    .join(band_genres, band_genres.c.band_id == Event.band_id)
                    .where(band_genres.c.genre_id.in_(disliked_genre_ids))
                )
            )
        )

    stmt = (
        select(Event)
        .where(and_(*conditions))
        .order_by(Event.event_date.is_(None), Event.event_date, Event.beginn)
        .limit(limit)
    )

    events = session.scalars(stmt).all()
    for event in events:
        markup = _event_markup(event)

        _send_band_sticker(event, user.chat_id)
        message = telegram_bot.send_message(
            chat_id=user.chat_id, text=event.get_message_text(), reply_markup=markup
        )

        observed_event = Observed(event_id=event.id, message_id=message.id)
        user.observed.append(observed_event)
        session.commit()
