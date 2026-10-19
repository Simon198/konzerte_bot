"""Unit tests for ``telegram.send_events``."""

import uuid
from datetime import date

from models.band import Band
from models.event import Event, Source
from telegram import send_events


def _event(**overrides) -> Event:
    defaults = dict(
        id=uuid.uuid4(),
        dto_id="1",
        source=Source.BATSCHKAPP,
        band=Band(name="A"),
        city="F",
        location="L",
        event_date=date(2026, 5, 10),
    )
    defaults.update(overrides)
    return Event(**defaults)


def test_event_markup_builds_buttons():
    event = _event()
    markup = send_events._event_markup(event)

    assert len(markup.keyboard) == 1
    buttons = markup.keyboard[0]
    assert buttons[0].text == "✅ Interesse"
    assert buttons[0].callback_data == f"interested;{event.id}"
    assert buttons[1].text == "❌ Kein Interesse"
    assert buttons[1].callback_data == f"not_interested;{event.id}"


def test_event_markup_adds_hoerprobe_button_above_interest_buttons():
    event = _event(band=Band(name="A", audio_sample="https://www.youtube.com/watch?v=abc"))
    markup = send_events._event_markup(event)

    assert len(markup.keyboard) == 2
    hoerprobe_row = markup.keyboard[0]
    assert len(hoerprobe_row) == 1
    assert hoerprobe_row[0].text == "Hörprobe"
    assert hoerprobe_row[0].url == "https://www.youtube.com/watch?v=abc"

    interest_row = markup.keyboard[1]
    assert interest_row[0].text == "✅ Interesse"
    assert interest_row[0].callback_data == f"interested;{event.id}"
    assert interest_row[1].text == "❌ Kein Interesse"
    assert interest_row[1].callback_data == f"not_interested;{event.id}"


def test_event_markup_skips_hoerprobe_without_audio_sample():
    markup = send_events._event_markup(_event(band=Band(name="A", audio_sample=None)))

    assert len(markup.keyboard) == 1
    assert markup.keyboard[0][0].text == "✅ Interesse"
