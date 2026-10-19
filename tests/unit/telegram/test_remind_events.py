"""Unit tests for ``telegram.remind_events``."""

from datetime import date, time

from models.band import Band
from models.event import Event, Source
from telegram import remind_events


def _event(**overrides):
    defaults = dict(
        dto_id="1",
        source=Source.BATSCHKAPP,
        band=Band(name="Band A"),
        city="Frankfurt",
        location="Batschkapp",
        event_date=date(2026, 5, 10),
    )
    defaults.update(overrides)
    return Event(**defaults)


class TestReminderTodayText:
    def test_builds_message(self):
        text = remind_events._reminder_today_text(_event())
        assert text == (
            "ERINNERUNG: Heute tritt auf\n10.05.2026 - Band A (Frankfurt-Batschkapp)"
        )


class TestReminderWeekText:
    def test_builds_message(self):
        text = remind_events._reminder_week_text(_event(admission=time(17, 30)))
        assert "In einer Woche tritt auf" in text
        assert "Einlass: 17:30 Uhr" in text
        assert "Falls du noch keine Karte besitzt" in text
