"""Integration tests for ``telegram.send_events``."""

import types
from datetime import date

import pytest

from models.event import Event, Source
from models.user import Observed, SourceUnsubscription, User
from telegram import send_events

pytestmark = pytest.mark.integration


class TestSendEventsToUser:
    def test_sends_only_unobserved_and_subscribed(self, wire, fake_bot):
        wire(send_events)
        observed = Event(
            dto_id="1", source=Source.BATSCHKAPP, band="Observed", city="F",
            location="L", event_date=date(2026, 6, 1),
        )
        unsubscribed = Event(
            dto_id="2", source=Source.FESTHALLE, band="Unsubscribed", city="F",
            location="L", event_date=date(2026, 6, 2),
        )
        candidate = Event(
            dto_id="3", source=Source.BATSCHKAPP, band="Band C", city="F",
            location="L", event_date=date(2026, 6, 3),
        )
        send_events.session.add_all([observed, unsubscribed, candidate])
        send_events.session.flush()

        user = User(id=1, chat_id=100)
        user.observed.append(Observed(event=observed, message_id=999))
        user.source_unsubscriptions.append(SourceUnsubscription(source=Source.FESTHALLE))
        send_events.session.add(user)
        send_events.session.commit()

        fake_bot.send_message.return_value = types.SimpleNamespace(id=1)

        send_events.send_events_to_user(user, limit=10)

        fake_bot.send_message.assert_called_once()
        assert "Band C" in fake_bot.send_message.call_args.kwargs["text"]
        # the sent event is now recorded as observed
        assert candidate.id in {o.event_id for o in user.observed}
