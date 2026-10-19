"""Integration tests for the storage functions in ``web_scraping.load_and_persist``."""

from datetime import date

import pytest
from sqlalchemy import func, select

from models.band import Band
from models.event import Event, Source
from models.user import Interest, Observed, User
from web_scraping import load_and_persist
from web_scraping.dto import EventDTO

pytestmark = pytest.mark.integration


def _dto(**overrides) -> EventDTO:
    defaults = dict(
        id="1",
        source=Source.BATSCHKAPP,
        band="Band A",
        city="Frankfurt",
        location="Batschkapp",
        date=date(2026, 5, 10),
        admission=None,
        beginn=None,
    )
    defaults.update(overrides)
    return EventDTO(**defaults)


class TestInsertEvent:
    def test_inserts_event_from_dto(self, wire):
        wire(load_and_persist)
        event_dto = _dto()
        event = load_and_persist._insert_event(event_dto, load_and_persist._get_or_create_band(event_dto.band))
        load_and_persist.session.flush()
        assert event.id is not None
        assert event.band_name == "Band A"


class TestInsertOrUpdateEvent:
    def test_inserts_then_updates_same_row(self, wire):
        wire(load_and_persist)
        first = load_and_persist._insert_or_update_event(_dto())
        load_and_persist.session.flush()

        updated = load_and_persist._insert_or_update_event(_dto(band="Band B"))
        load_and_persist.session.flush()

        assert updated is first
        assert updated.band_name == "Band B"
        count = load_and_persist.session.scalar(
            select(func.count()).select_from(Event).where(Event.dto_id == "1")
        )
        assert count == 1


class TestUpdateEvent:
    def test_change_notifies_interested_and_edits_observed(self, wire, fake_bot):
        wire(load_and_persist)

        event = Event(
            dto_id="1", source=Source.BATSCHKAPP, band=Band(name="Band A"), city="F",
            location="L", event_date=date(2026, 5, 10),
        )
        interested = User(id=1, chat_id=100, username="alice")
        observer = User(id=2, chat_id=200, username="bob")
        interested.interest.append(Interest(event=event))
        observer.observed.append(Observed(event=event, message_id=555))
        load_and_persist.session.add_all([event, interested, observer])
        load_and_persist.session.commit()

        load_and_persist._update_event(
            _dto(band="Band B"), event, load_and_persist._get_or_create_band("Band B")
        )

        assert event.band_name == "Band B"
        # the interested user is notified of the change
        fake_bot.send_message.assert_called_once()
        assert fake_bot.send_message.call_args.kwargs["chat_id"] == 100
        # the observed user's message is edited
        fake_bot.edit_message_text.assert_called_once()


class _NoopTqdm:
    def __init__(self, iterable=None, **kwargs):
        self.iterable = iterable

    def __iter__(self):
        return iter(self.iterable or [])

    def update(self, *args, **kwargs):
        pass

    def close(self):
        pass


class TestFillMissingAudioSamples:
    def test_fills_audio_sample_only_for_bands_without_one(self, wire, monkeypatch):
        wire(load_and_persist)
        missing = Band(name="Missing")
        filled = Band(name="Filled", audio_sample="https://www.youtube.com/watch?v=already")
        load_and_persist.session.add_all([missing, filled])
        load_and_persist.session.commit()

        monkeypatch.setattr(load_and_persist, "tqdm_admin_telegram", _NoopTqdm)
        monkeypatch.setattr(
            load_and_persist,
            "find_audio_sample",
            lambda name: "https://www.youtube.com/watch?v=abc" if name == "Missing" else None,
        )
        monkeypatch.setattr("time.sleep", lambda *args, **kwargs: None)

        load_and_persist._fill_missing_audio_samples()

        assert missing.audio_sample == "https://www.youtube.com/watch?v=abc"
        assert filled.audio_sample == "https://www.youtube.com/watch?v=already"
