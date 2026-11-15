"""Integration tests for ``telegram.send_events``."""

import types
from datetime import date

import pytest

from models.band import Band
from models.event import Event, Source
from models.genre import Genre
from models.user import Observed, SourceUnsubscription, GenreUnsubscription, User
from telegram import send_events

pytestmark = pytest.mark.integration


def _sticker_message(file_id="file-1", message_id=42):
    """A lightweight stand-in for the ``Message`` returned by ``send_sticker``."""
    return types.SimpleNamespace(
        id=message_id,
        sticker=types.SimpleNamespace(file_id=file_id),
    )


class TestCacheStickerFileId:
    def test_caches_on_first_use_and_reuses(self, wire, fake_bot, tmp_path):
        wire(send_events)
        image = tmp_path / "band.webp"
        image.write_bytes(b"fake-sticker")

        admin = User(id=1, chat_id=111, is_admin=True)
        band = Band(name="Band A", image_path=str(image))
        send_events.session.add_all([admin, band])
        send_events.session.commit()

        fake_bot.send_sticker.return_value = _sticker_message(
            file_id="file-1", message_id=7
        )

        assert send_events.cache_sticker_file_id(band, admin.chat_id) == "file-1"
        assert band.sticker_file_id == "file-1"
        # A second call returns the cached id without uploading again.
        assert send_events.cache_sticker_file_id(band, admin.chat_id) == "file-1"

        fake_bot.send_sticker.assert_called_once()
        fake_bot.delete_message.assert_called_once_with(
            chat_id=admin.chat_id, message_id=7
        )

    def test_returns_none_without_image(self, wire, fake_bot, tmp_path):
        wire(send_events)
        admin = User(id=1, chat_id=111, is_admin=True)
        band = Band(name="Band A", image_path="/does/not/exist.webp")
        send_events.session.add_all([admin, band])
        send_events.session.commit()

        assert send_events.cache_sticker_file_id(band, admin.chat_id) is None
        assert band.sticker_file_id is None
        fake_bot.send_sticker.assert_not_called()


class TestSendBandSticker:
    def test_first_send_uploads_directly_to_user_and_caches_id(
        self, wire, fake_bot, tmp_path
    ):
        wire(send_events)
        image = tmp_path / "band.webp"
        image.write_bytes(b"fake-sticker")

        admin = User(id=1, chat_id=111, is_admin=True)
        user = User(id=2, chat_id=222, is_admin=False)
        band = Band(name="Band A", image_path=str(image))
        event = Event(
            dto_id="1", source=Source.BATSCHKAPP, band=band, city="F",
            location="L", event_date=date(2026, 6, 1),
        )
        send_events.session.add_all([admin, user, event])
        send_events.session.commit()

        fake_bot.send_sticker.return_value = _sticker_message(
            file_id="file-1", message_id=42
        )

        send_events._send_band_sticker(event, user.chat_id)

        # The file is uploaded directly to the user (not the admin) ...
        call = fake_bot.send_sticker.call_args
        assert call.kwargs["chat_id"] == user.chat_id
        # ... and the returned file_id is cached for future sends.
        assert band.sticker_file_id == "file-1"
        fake_bot.delete_message.assert_not_called()

    def test_second_send_reuses_cached_file_id(self, wire, fake_bot, tmp_path):
        wire(send_events)
        image = tmp_path / "band.webp"
        image.write_bytes(b"fake-sticker")

        admin = User(id=1, chat_id=111, is_admin=True)
        user = User(id=2, chat_id=222, is_admin=False)
        band = Band(
            name="Band A", image_path=str(image), sticker_file_id="file-1"
        )
        event = Event(
            dto_id="1", source=Source.BATSCHKAPP, band=band, city="F",
            location="L", event_date=date(2026, 6, 1),
        )
        send_events.session.add_all([admin, user, event])
        send_events.session.commit()

        send_events._send_band_sticker(event, user.chat_id)

        fake_bot.send_sticker.assert_called_once_with(
            chat_id=user.chat_id, sticker="file-1"
        )
        fake_bot.delete_message.assert_not_called()

    def test_rejected_cached_file_id_is_reuploaded(self, wire, fake_bot, tmp_path):
        wire(send_events)
        image = tmp_path / "band.webp"
        image.write_bytes(b"fake-sticker")

        admin = User(id=1, chat_id=111, is_admin=True)
        user = User(id=2, chat_id=222, is_admin=False)
        band = Band(
            name="Band A", image_path=str(image), sticker_file_id="stale-id"
        )
        event = Event(
            dto_id="1", source=Source.BATSCHKAPP, band=band, city="F",
            location="L", event_date=date(2026, 6, 1),
        )
        send_events.session.add_all([admin, user, event])
        send_events.session.commit()

        # The stale id is rejected; the file is re-uploaded to the user.
        fake_bot.send_sticker.side_effect = [
            Exception("Bad Request: file_id not found"),
            _sticker_message(file_id="fresh-id", message_id=43),
        ]

        send_events._send_band_sticker(event, user.chat_id)

        stale_call, upload_call = fake_bot.send_sticker.call_args_list
        assert stale_call.kwargs["sticker"] == "stale-id"
        # The re-upload goes directly to the user, not the admin.
        assert upload_call.kwargs["chat_id"] == user.chat_id
        assert band.sticker_file_id == "fresh-id"
        fake_bot.delete_message.assert_not_called()


class TestSendEventsToUser:
    def test_sends_only_unobserved_and_subscribed(self, wire, fake_bot):
        wire(send_events)
        observed = Event(
            dto_id="1", source=Source.BATSCHKAPP, band=Band(name="Observed"), city="F",
            location="L", event_date=date(2026, 6, 1),
        )
        unsubscribed = Event(
            dto_id="2", source=Source.FESTHALLE, band=Band(name="Unsubscribed"), city="F",
            location="L", event_date=date(2026, 6, 2),
        )
        candidate = Event(
            dto_id="3", source=Source.BATSCHKAPP, band=Band(name="Band C"), city="F",
            location="L", event_date=date(2026, 6, 3),
        )
        send_events.session.add_all([observed, unsubscribed, candidate])
        send_events.session.flush()

        user = User(id=1, chat_id=100)
        user.observed.append(Observed(event=observed, message_id=999))
        user.source_unsubscriptions.append(SourceUnsubscription(source=Source.FESTHALLE))
        send_events.session.add(user)
        send_events.session.commit()

        fake_bot.send_message.return_value = types.SimpleNamespace(id=1)

        send_events.send_events_to_user(user, limit=10)

        fake_bot.send_message.assert_called_once()
        assert "Band C" in fake_bot.send_message.call_args.kwargs["text"]
        # the sent event is now recorded as observed
        assert candidate.id in {o.event_id for o in user.observed}

    def test_excludes_events_with_disliked_genre(self, wire, fake_bot):
        wire(send_events)
        metal = Genre(id=1, name="Metal")
        blocked = Event(
            dto_id="1", source=Source.BATSCHKAPP,
            band=Band(name="Blocked", genres=[metal]), city="F",
            location="L", event_date=date(2026, 6, 1),
        )
        candidate = Event(
            dto_id="2", source=Source.BATSCHKAPP,
            band=Band(name="Band C", genres=[Genre(id=2, name="Rock")]), city="F",
            location="L", event_date=date(2026, 6, 2),
        )
        send_events.session.add_all([blocked, candidate])
        send_events.session.flush()

        user = User(id=1, chat_id=100)
        user.genre_unsubscriptions.append(GenreUnsubscription(genre_id=metal.id))
        send_events.session.add(user)
        send_events.session.commit()

        fake_bot.send_message.return_value = types.SimpleNamespace(id=1)

        send_events.send_events_to_user(user, limit=10)

        fake_bot.send_message.assert_called_once()
        assert "Band C" in fake_bot.send_message.call_args.kwargs["text"]
