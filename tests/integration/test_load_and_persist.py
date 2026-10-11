"""Integration tests for the storage functions in ``web_scraping.load_and_persist``."""

from datetime import date

import pytest
from sqlalchemy import func, select

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
        event = load_and_persist._insert_event(_dto())
        load_and_persist.session.flush()
        assert event.id is not None
        assert event.band == "Band A"


class TestInsertOrUpdateEvent:
    def test_inserts_then_updates_same_row(self, wire):
        wire(load_and_persist)
        first = load_and_persist._insert_or_update_event(_dto())
        load_and_persist.session.flush()

        updated = load_and_persist._insert_or_update_event(_dto(band="Band B"))
        load_and_persist.session.flush()

        assert updated is first
        assert updated.band == "Band B"
        count = load_and_persist.session.scalar(
            select(func.count()).select_from(Event).where(Event.dto_id == "1")
        )
        assert count == 1


class TestUpdateEvent:
    def test_change_notifies_interested_and_edits_observed(self, wire, fake_bot):
        wire(load_and_persist)

        event = Event(
            dto_id="1", source=Source.BATSCHKAPP, band="Band A", city="F",
            location="L", event_date=date(2026, 5, 10),
        )
        interested = User(id=1, chat_id=100, username="alice")
        observer = User(id=2, chat_id=200, username="bob")
        interested.interest.append(Interest(event=event))
        observer.observed.append(Observed(event=event, message_id=555))
        load_and_persist.session.add_all([event, interested, observer])
        load_and_persist.session.commit()

        load_and_persist._update_event(_dto(band="Band B"), event)

        assert event.band == "Band B"
        # the interested user is notified of the change
        fake_bot.send_message.assert_called_once()
        assert fake_bot.send_message.call_args.kwargs["chat_id"] == 100
        # the observed user's message is edited
        fake_bot.edit_message_text.assert_called_once()
