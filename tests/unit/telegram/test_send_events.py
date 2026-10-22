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
    event = _event(band=Band(name="A", audio_sample="https://www.deezer.com/track/abc"))
    markup = send_events._event_markup(event)

    assert len(markup.keyboard) == 2
    hoerprobe_row = markup.keyboard[0]
    assert len(hoerprobe_row) == 1
    assert hoerprobe_row[0].text == "Hörprobe"
    assert hoerprobe_row[0].url == "https://www.deezer.com/track/abc"

    interest_row = markup.keyboard[1]
    assert interest_row[0].text == "✅ Interesse"
    assert interest_row[0].callback_data == f"interested;{event.id}"
    assert interest_row[1].text == "❌ Kein Interesse"
    assert interest_row[1].callback_data == f"not_interested;{event.id}"


def test_event_markup_skips_hoerprobe_without_audio_sample():
    markup = send_events._event_markup(_event(band=Band(name="A", audio_sample=None)))

    assert len(markup.keyboard) == 1
    assert markup.keyboard[0][0].text == "✅ Interesse"


def test_event_markup_adds_tickets_button_next_to_hoerprobe():
    event = _event(
        band=Band(name="A", audio_sample="https://www.deezer.com/track/abc"),
        url="https://www.batschkapp.net/events/example",
    )
    markup = send_events._event_markup(event)

    assert len(markup.keyboard) == 2
    link_row = markup.keyboard[0]
    assert len(link_row) == 2
    assert link_row[0].text == "Hörprobe"
    assert link_row[0].url == "https://www.deezer.com/track/abc"
    assert link_row[1].text == "Tickets"
    assert link_row[1].url == "https://www.batschkapp.net/events/example"

    interest_row = markup.keyboard[1]
    assert interest_row[0].text == "✅ Interesse"
    assert interest_row[1].text == "❌ Kein Interesse"


def test_event_markup_adds_tickets_button_without_audio_sample():
    event = _event(url="https://www.batschkapp.net/events/example")
    markup = send_events._event_markup(event)

    assert len(markup.keyboard) == 2
    link_row = markup.keyboard[0]
    assert len(link_row) == 1
    assert link_row[0].text == "Tickets"
    assert link_row[0].url == "https://www.batschkapp.net/events/example"


def test_event_markup_skips_tickets_without_url():
    markup = send_events._event_markup(
        _event(band=Band(name="A", audio_sample="https://www.deezer.com/track/abc"))
    )

    assert len(markup.keyboard) == 2
    assert markup.keyboard[0][0].text == "Hörprobe"


def test_band_image_path_returns_existing_file(tmp_path):
    image = tmp_path / "band.jpg"
    image.write_bytes(b"fake-image")

    event = _event(band=Band(name="A", image_path=str(image)))

    assert send_events._band_image_path(event) == str(image)


def test_band_image_path_returns_none_when_missing(tmp_path):
    missing = tmp_path / "does-not-exist.jpg"

    event = _event(band=Band(name="A", image_path=str(missing)))

    assert send_events._band_image_path(event) is None


def test_band_image_path_returns_none_without_image_path():
    assert send_events._band_image_path(_event(band=Band(name="A"))) is None
