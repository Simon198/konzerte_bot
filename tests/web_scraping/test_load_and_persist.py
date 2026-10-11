"""Unit tests for the event upsert / change-detection logic in ``load_and_persist``."""

from datetime import date

from sqlalchemy import func, select

from models.event import Event, Source
from models.user import Interest, User
from web_scraping import load_and_persist
from web_scraping.dto import EventDTO


def make_dto(**overrides) -> EventDTO:
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


def make_event(**overrides) -> Event:
    defaults = dict(
        dto_id="1",
        source=Source.BATSCHKAPP,
        band="Band A",
        city="Frankfurt",
        location="Batschkapp",
        event_date=date(2026, 5, 10),
    )
    defaults.update(overrides)
    return Event(**defaults)


class TestUpdateEvent:
    def test_no_changes_returns_same_event(self):
        event = make_event()
        assert load_and_persist._update_event(make_dto(), event) is event

    def test_detects_band_change(self):
        event = make_event()
        load_and_persist._update_event(make_dto(band="Band B"), event)
        assert event.band == "Band B"

    def test_detects_date_change(self):
        event = make_event()
        load_and_persist._update_event(make_dto(date=date(2026, 6, 1)), event)
        assert event.event_date == date(2026, 6, 1)


class TestInsertEvent:
    def test_inserts_from_dto(self, session, monkeypatch):
        monkeypatch.setattr(load_and_persist, "session", session)
        event = load_and_persist._insert_event(make_dto())
        session.flush()
        assert event.id is not None
        assert event.band == "Band A"
        assert event.city == "Frankfurt"


class TestInsertOrUpdateEvent:
    def test_inserts_then_updates_same_row(self, session, monkeypatch):
        monkeypatch.setattr(load_and_persist, "session", session)
        first = load_and_persist._insert_or_update_event(make_dto())
        session.flush()

        updated = load_and_persist._insert_or_update_event(make_dto(band="Band B"))
        session.flush()

        assert updated is first
        assert updated.band == "Band B"

        count = session.scalar(
            select(func.count()).select_from(Event).where(Event.dto_id == "1")
        )
        assert count == 1


class TestSendMessageToInterestedUsers:
    def test_sends_changes_to_interested_user(self, monkeypatch):
        sent = []
        monkeypatch.setattr(
            load_and_persist.telegram_bot,
            "send_message",
            lambda chat_id, text: sent.append((chat_id, text)),
        )
        event = make_event()
        event.interest.append(Interest(user=User(id=1, chat_id=100)))

        load_and_persist._send_message_to_interested_users(
            event, {"band": ("Band A", "Band B")}
        )

        assert len(sent) == 1
        chat_id, text = sent[0]
        assert chat_id == 100
        assert "Band: Band A -> Band B" in text

    def test_skips_unknown_attributes(self, monkeypatch):
        sent = []
        monkeypatch.setattr(
            load_and_persist.telegram_bot,
            "send_message",
            lambda chat_id, text: sent.append((chat_id, text)),
        )
        event = make_event()
        event.interest.append(Interest(user=User(id=1, chat_id=100)))

        load_and_persist._send_message_to_interested_users(
            event, {"not_a_field": ("a", "b")}
        )

        assert sent == []
