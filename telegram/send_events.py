import logging
import os
import threading

from sqlalchemy import and_, not_, select
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from models.band import Band
from models.event import Event
from models.genre import band_genres
from models.user import (
    GenreUnsubscription,
    Interest,
    Observed,
    SourceUnsubscription,
    User,
)
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
    event: Event, is_interested: bool | None = None, is_admin: bool = False
) -> InlineKeyboardMarkup:
    """Build the interest reply keyboard for an event (pure).

    ``is_interested`` reflects the user's current decision:
    - ``None`` (undecided): show "Interesse" and "Kein Interesse" (skip),
    - ``True``: show only "zurücknehmen",
    - ``False``: show only "Interesse", so a skip can still be reversed.

    Admins additionally get a "Broadcast" button to the left of the interest
    buttons once they are interested in the event.
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
        buttons = []
        if is_admin:
            buttons.append(
                InlineKeyboardButton(
                    "📣 Broadcast", callback_data=f"broadcast;{event.id}"
                )
            )
        buttons.append(
            InlineKeyboardButton(
                "❌ Interesse zurücknehmen",
                callback_data=f"not_interested;{event.id}",
            )
        )
        markup.add(*buttons)
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


def _upload_sticker_to_admin(image_path: str, admin_chat_id: int) -> str | None:  # pragma: no cover - Telegram I/O
    """Upload the sticker at ``image_path`` to the admin chat and return its file_id.

    Telegram ``file_id``s are bot-scoped but chat-agnostic, so the file only has
    to be uploaded once and the id can then be reused for every user. The upload
    is sent with notifications disabled and deleted immediately so the admin is
    not spammed. Returns ``None`` if the upload fails.
    """
    message = None
    try:
        with open(image_path, "rb") as sticker:
            message = telegram_bot.send_sticker(
                chat_id=admin_chat_id,
                sticker=sticker,
                disable_notification=True,
            )
        return message.sticker.file_id
    except Exception:
        logger.exception("Could not upload sticker %r to the admin", image_path)
        return None
    finally:
        if message is not None:
            try:
                telegram_bot.delete_message(
                    chat_id=admin_chat_id, message_id=message.id
                )
            except Exception:
                logger.exception(
                    "Could not delete sticker upload message for %r", image_path
                )


def cache_sticker_file_id(band: Band, admin_chat_id: int) -> str | None:  # pragma: no cover - DB + Telegram I/O
    """Return ``band``'s sticker ``file_id``, uploading and caching it on first use.

    Used by the daily load to pre-warm file_ids: the sticker is uploaded once to
    ``admin_chat_id`` (silently) so later event sends can reuse the id. Returns
    ``None`` if the band has no image on disk or the upload fails.
    """
    if band.sticker_file_id:
        return band.sticker_file_id
    image_path = band.image_path
    if not image_path or not os.path.isfile(image_path):
        return None
    file_id = _upload_sticker_to_admin(image_path, admin_chat_id)
    if file_id is not None:
        band.sticker_file_id = file_id
        session.commit()
    return file_id


def _send_band_sticker(event: Event, chat_id: int):  # pragma: no cover - Telegram I/O
    """Send the band's image as a small sticker.

    The sticker is sent by ``file_id`` (a lightweight API call) whenever a cached
    id is available. Otherwise the file is uploaded directly to the user and the
    returned id is cached, so every later user is served from the cache. A cached
    id that Telegram rejects is cleared and the file re-uploaded to the user.
    """
    band = event.band
    image_path = _band_image_path(event)
    if band is None or image_path is None:
        return

    if band.sticker_file_id is not None:
        try:
            telegram_bot.send_sticker(chat_id=chat_id, sticker=band.sticker_file_id)
            return
        except Exception:
            logger.exception(
                "Cached sticker file_id was rejected for %r; re-uploading",
                event.band_name,
            )
            band.sticker_file_id = None

    # No valid cached id: upload the file directly to this user and cache the
    # returned id so subsequent users are served from the cache.
    try:
        with open(image_path, "rb") as sticker:
            message = telegram_bot.send_sticker(chat_id=chat_id, sticker=sticker)
        band.sticker_file_id = message.sticker.file_id
        session.commit()
    except Exception:
        logger.exception("Could not send band sticker for %r", event.band_name)
        session.rollback()
        band.sticker_file_id = None


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


def broadcast_event_to_users(
    event: Event, exclude_user_id: int | None = None
):  # pragma: no cover - DB + Telegram I/O
    """Send ``event`` to every user a broadcast targets.

    A broadcast reaches users who are not interested in the event, have not yet
    been sent the event, and have not unsubscribed from the event's source or any
    of its band's genres. ``exclude_user_id`` (the admin triggering the
    broadcast) is skipped as well, defensively.
    """
    band_genre_ids = select(band_genres.c.genre_id).where(
        band_genres.c.band_id == event.band_id
    )

    conditions = [
        not_(
            User.id.in_(
                select(Interest.user_id).where(Interest.event_id == event.id)
            )
        ),
        not_(
            User.id.in_(
                select(Observed.user_id).where(Observed.event_id == event.id)
            )
        ),
        not_(
            User.id.in_(
                select(SourceUnsubscription.user_id).where(
                    SourceUnsubscription.source == event.source
                )
            )
        ),
        not_(
            User.id.in_(
                select(GenreUnsubscription.user_id).where(
                    GenreUnsubscription.genre_id.in_(band_genre_ids)
                )
            )
        ),
    ]
    if exclude_user_id is not None:
        conditions.append(User.id != exclude_user_id)

    users = session.scalars(select(User).where(and_(*conditions))).all()
    for user in users:
        markup = _event_markup(event)

        _send_band_sticker(event, user.chat_id)
        message = telegram_bot.send_message(
            chat_id=user.chat_id, text=event.get_message_text(), reply_markup=markup
        )

        # ``Observed`` has a composite primary key; skip the insert if the event
        # was already recorded (defensive, in case a concurrent send recorded it).
        if session.get(Observed, (user.id, event.id)) is None:
            user.observed.append(Observed(event_id=event.id, message_id=message.id))
            session.commit()
