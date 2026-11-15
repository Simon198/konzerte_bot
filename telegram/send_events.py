import logging
import os
import threading

from sqlalchemy import and_, not_, select
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from models.event import Event
from models.genre import band_genres
from models.user import Observed, User
from repository import session

from . import telegram_bot

logger = logging.getLogger(__name__)

# Sending an event takes time (sticker upload + message). While a send is still
# in flight, the event is not yet recorded as ``Observed``, so a second ``/go``
# (or a callback that advances the queue) would query and send the *same* event
# again. Serialising sends per user prevents that duplicate.
_user_send_locks: dict[int, threading.Lock] = {}
_user_send_locks_guard = threading.Lock()


def _lock_for_user(user_id: int) -> threading.Lock:
    with _user_send_locks_guard:
        lock = _user_send_locks.get(user_id)
        if lock is None:
            lock = threading.Lock()
            _user_send_locks[user_id] = lock
        return lock


def _event_markup(
    event: Event, is_interested: bool | None = None
) -> InlineKeyboardMarkup:
    """Build the interest reply keyboard for an event (pure).

    ``is_interested`` reflects the user's current decision:
    - ``None`` (undecided): show "Interesse" and "Kein Interesse" (skip),
    - ``True``: show only "zurücknehmen",
    - ``False``: show only "Interesse", so a skip can still be reversed.
    """
    markup = InlineKeyboardMarkup()

    link_buttons = []
    audio_sample = event.band.audio_sample if event.band is not None else None
    if audio_sample:
        link_buttons.append(InlineKeyboardButton("Hörprobe", url=audio_sample))
    if event.url:
        link_buttons.append(InlineKeyboardButton("Tickets", url=event.url))
    if link_buttons:
        markup.add(*link_buttons)

    if is_interested:
        markup.add(
            InlineKeyboardButton(
                "❌ Interesse zurücknehmen",
                callback_data=f"not_interested;{event.id}",
            )
        )
    elif is_interested is False:
        markup.add(
            InlineKeyboardButton(
                "✅ Interesse", callback_data=f"interested;{event.id}"
            )
        )
    else:
        markup.add(
            InlineKeyboardButton(
                "✅ Interesse", callback_data=f"interested;{event.id}"
            ),
            InlineKeyboardButton(
                "❌ Kein Interesse", callback_data=f"not_interested;{event.id}"
            ),
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

    # Serialise sends for this user. Concurrent ``/go`` commands (or a callback
    # advancing the queue) otherwise both see the event as unobserved and send
    # it twice, and the second ``Observed`` insert then violates the composite
    # primary key on ``(user_id, event_id)``.
    with _lock_for_user(user.id):
        events = session.scalars(stmt).all()
        for event in events:
            markup = _event_markup(event)

            _send_band_sticker(event, user.chat_id)
            message = telegram_bot.send_message(
                chat_id=user.chat_id, text=event.get_message_text(), reply_markup=markup
            )

            # ``Observed`` has a composite primary key; skip the insert if the
            # event was already recorded (defensive, in case the event slipped
            # through the "unobserved" filter above).
            if session.get(Observed, (user.id, event.id)) is None:
                user.observed.append(Observed(event_id=event.id, message_id=message.id))
                session.commit()
