"""Unit tests for the pure helpers in ``telegram.message_handler``."""

import uuid
from datetime import date

from models.event import Event, Source
from telegram import message_handler


class TestParseLimit:
    def test_parses_number(self):
        assert message_handler._parse_limit("/next 5", "next", 100) == 5

    def test_defaults_when_missing(self):
        assert message_handler._parse_limit("/next", "next", 100) == 100

    def test_defaults_when_not_a_number(self):
        assert message_handler._parse_limit("/next abc", "next", 100) == 100


class TestExtractFeatureText:
    def test_extracts_text(self):
        assert message_handler._extract_feature_text("/feature Mehr Metal") == "Mehr Metal"

    def test_empty_when_no_text(self):
        assert message_handler._extract_feature_text("/feature") == ""


def _event(band, event_date=date(2026, 5, 10)):
    return Event(
        id=uuid.uuid4(),
        dto_id=band,
        source=Source.BATSCHKAPP,
        band=band,
        city="F",
        location="L",
        event_date=event_date,
    )


class TestBuildPairingsLines:
    def test_ignores_requesting_user(self):
        event = _event("Metallica")
        rows = [(event, 1, "admin"), (event, 2, "bob")]
        text = message_handler._build_pairings_lines(rows, current_user_id=1)
        assert "@bob" in text
        assert "@admin" not in text

    def test_no_pairings_returns_none(self):
        event = _event("Metallica")
        rows = [(event, 1, "admin")]
        assert message_handler._build_pairings_lines(rows, current_user_id=1) is None

    def test_username_fallback_for_missing_username(self):
        event = _event("Metallica")
        rows = [(event, 2, None)]
        text = message_handler._build_pairings_lines(rows, current_user_id=1)
        assert "Nutzer 2" in text

    def test_groups_multiple_users_on_same_event(self):
        event = _event("Metallica")
        rows = [(event, 2, "bob"), (event, 3, "carol")]
        text = message_handler._build_pairings_lines(rows, current_user_id=1)
        assert "Metallica" in text
        assert "10.05.2026" in text
        assert "@bob" in text
        assert "@carol" in text
