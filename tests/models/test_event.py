"""Unit tests for the ``Event`` ORM model's message formatting helpers."""

from datetime import date, time

from models.event import Event, Source


def make_event(**overrides) -> Event:
    defaults = dict(
        dto_id="1",
        source=Source.BATSCHKAPP,
        band="Metallica",
        city="Frankfurt",
        location="Festhalle",
    )
    defaults.update(overrides)
    return Event(**defaults)


class TestGetGermanDate:
    def test_none_date(self):
        assert make_event(event_date=None).get_german_date() == "(?)"

    def test_formatted_date(self):
        assert make_event(event_date=date(2026, 5, 10)).get_german_date() == "10.05.2026"

    def test_padded_day_and_month(self):
        assert make_event(event_date=date(2026, 1, 5)).get_german_date() == "05.01.2026"


class TestTimes:
    def test_get_admission_text(self):
        assert make_event(admission=time(17, 30)).get_admission_text() == "17:30 Uhr"

    def test_get_beginn_text(self):
        assert make_event(beginn=time(20, 0)).get_beginn_text() == "20:00 Uhr"


class TestGetShortMessageText:
    def test_with_date(self):
        event = make_event(event_date=date(2026, 5, 10))
        assert event.get_short_message_text() == "10.05.2026 - Metallica (Frankfurt-Festhalle)"

    def test_without_date(self):
        event = make_event(event_date=None)
        assert event.get_short_message_text() == "(?) - Metallica (Frankfurt-Festhalle)"


class TestGetMessageText:
    def test_only_band_information(self):
        event = make_event(event_date=date(2026, 5, 10))
        assert event.get_message_text() == "10.05.2026 - Metallica (Frankfurt-Festhalle)"

    def test_with_subtitle(self):
        text = make_event(subtitle="Support: Ghost").get_message_text()
        assert "Support: Ghost" in text

    def test_with_admission_and_beginn(self):
        event = make_event(admission=time(17, 30), beginn=time(20, 0))
        text = event.get_message_text()
        assert "Einlass: 17:30 Uhr" in text
        assert "Beginn: 20:00 Uhr" in text
        assert "Einlass: 17:30 Uhr; Beginn: 20:00 Uhr" in text

    def test_with_admission_only(self):
        text = make_event(admission=time(17, 30)).get_message_text()
        assert "Einlass: 17:30 Uhr" in text
        assert "Beginn:" not in text

    def test_with_hint_and_status(self):
        text = make_event(hint="Ausverkauft", status="Abgesagt").get_message_text()
        assert "Ausverkauft" in text
        assert "Status: Abgesagt" in text

    def test_full_message_exact(self):
        event = make_event(
            event_date=date(2026, 5, 10),
            subtitle="World Tour",
            admission=time(17, 30),
            beginn=time(20, 0),
            hint="Ausverkauft",
            status="Abgesagt",
        )
        assert event.get_message_text() == (
            "10.05.2026 - Metallica (Frankfurt-Festhalle)\n"
            "World Tour\n"
            "Einlass: 17:30 Uhr; Beginn: 20:00 Uhr\n"
            "Ausverkauft\n"
            "Status: Abgesagt"
        )
