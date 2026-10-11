"""Integration tests for ``telegram.remind_events``."""

from datetime import date

import pytest

from models.event import Event, Source
from models.user import Interest, User
from telegram import remind_events

pytestmark = pytest.mark.integration


class TestRemindEvents:
    def test_reminds_interested_users(self, wire, fake_bot):
        wire(remind_events)
        event = Event(
            dto_id="1", source=Source.BATSCHKAPP, band="Band A", city="F",
            location="L", event_date=date.today(),
        )
        user = User(id=1, chat_id=100)
        user.interest.append(Interest(event=event))
        remind_events.session.add(user)
        remind_events.session.commit()

        remind_events.remind_events()

        fake_bot.send_message.assert_called_once()
        assert "ERINNERUNG: Heute tritt auf" in fake_bot.send_message.call_args.kwargs["text"]
