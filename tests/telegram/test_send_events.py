"""Unit tests for ``telegram.send_events``."""

import uuid
from datetime import date

from models.event import Event, Source
from telegram import send_events


def test_event_markup_builds_buttons():
    event = Event(
        id=uuid.uuid4(),
        dto_id="1",
        source=Source.BATSCHKAPP,
        band="A",
        city="F",
        location="L",
        event_date=date(2026, 5, 10),
    )
    markup = send_events._event_markup(event)

    buttons = markup.keyboard[0]
    assert buttons[0].text == "✅ Interesse"
    assert buttons[0].callback_data == f"interested;{event.id}"
    assert buttons[1].text == "❌ Kein Interesse"
    assert buttons[1].callback_data == f"not_interested;{event.id}"
