"""Unit tests for the pure transformation helpers in ``web_scraping.load_and_persist``."""

from datetime import date, time

from models.event import Event, Source
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


class TestEventFromDto:
    def test_maps_all_fields(self):
        dto = make_dto(
            admission=time(17, 30),
            beginn=time(20, 0),
            hint="Ausverkauft",
            subtitle="Sub",
            status="Status",
        )
        event = load_and_persist._event_from_dto(dto)
        assert event.dto_id == "1"
        assert event.source == Source.BATSCHKAPP
        assert event.band == "Band A"
        assert event.city == "Frankfurt"
        assert event.location == "Batschkapp"
        assert event.event_date == date(2026, 5, 10)
        assert event.admission == time(17, 30)
        assert event.beginn == time(20, 0)
        assert event.hint == "Ausverkauft"
        assert event.subtitle == "Sub"
        assert event.status == "Status"


class TestDiffEvent:
    def test_no_changes(self):
        assert load_and_persist._diff_event(make_dto(), make_event()) == {}

    def test_detects_band_change(self):
        changes = load_and_persist._diff_event(make_dto(band="Band B"), make_event())
        assert changes == {"band": ("Band A", "Band B")}

    def test_detects_date_change(self):
        changes = load_and_persist._diff_event(
            make_dto(date=date(2026, 6, 1)), make_event()
        )
        assert changes == {"event_date": (date(2026, 5, 10), date(2026, 6, 1))}


class TestFormatChangeTexts:
    def test_translates_known_fields(self):
        changes = {
            "band": ("Band A", "Band B"),
            "event_date": (date(2026, 5, 10), date(2026, 6, 1)),
        }
        assert load_and_persist._format_change_texts(changes) == [
            "Band: Band A -> Band B",
            "Datum: 2026-05-10 -> 2026-06-01",
        ]

    def test_skips_unknown_fields(self):
        assert load_and_persist._format_change_texts({"not_a_field": ("a", "b")}) == []


class TestFormatChangeMessage:
    def test_builds_summary(self):
        text = load_and_persist._format_change_message(
            make_event(), ["Band: Band A -> Band B"]
        )
        assert "Es gibt folgende Änderungen zu Band A" in text
        assert "Band: Band A -> Band B" in text
