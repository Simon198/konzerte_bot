"""Integration tests for ``telegram.callback_query_handler``."""

from datetime import date

import pytest

from models.band import Band
from models.event import Event, Source
from models.user import Interest, User
from telegram import callback_query_handler, prodcast_message, send_events
from telegram.callback_data import CallbackData

pytestmark = pytest.mark.integration


def _event():
    return Event(
        dto_id="1", source=Source.BATSCHKAPP, band=Band(name="Band A"), city="F",
        location="L", event_date=date(2026, 6, 1),
    )


class TestInterested:
    def test_adds_interest(self, wire, make_callback_query, fake_bot):
        wire(callback_query_handler, prodcast_message, send_events)
        event = _event()
        user = User(id=1, chat_id=100, username="alice", consent_given=True)
        callback_query_handler.session.add_all([event, user])
        callback_query_handler.session.commit()

        callback_query_handler.handle_callback_query(
            make_callback_query(f"{CallbackData.INTERESTED.value};{event.id}")
        )

        assert len(user.interest) == 1
        assert user.interest[0].event_id == event.id
        fake_bot.edit_message_reply_markup.assert_called_once()


class TestNotInterested:
    def test_removes_interest(self, wire, make_callback_query, fake_bot):
        wire(callback_query_handler, prodcast_message, send_events)
        event = _event()
        user = User(id=1, chat_id=100, username="alice", consent_given=True)
        user.interest.append(Interest(event=event))
        callback_query_handler.session.add(user)
        callback_query_handler.session.commit()

        callback_query_handler.handle_callback_query(
            make_callback_query(f"{CallbackData.NOT_INTERESTED.value};{event.id}")
        )

        assert user.interest == []


class TestConsent:
    def test_accept_marks_consent(self, wire, make_callback_query, fake_bot):
        wire(callback_query_handler, prodcast_message, send_events)
        callback_query_handler.session.add(User(id=1, chat_id=100, username="alice"))
        callback_query_handler.session.commit()

        callback_query_handler.handle_callback_query(
            make_callback_query(f"{CallbackData.CONSENT.value};accept")
        )

        user = callback_query_handler.session.get(User, 1)
        assert user.consent_given is True
        assert user.consent_version is not None

    def test_decline_does_not_grant_consent(self, wire, make_callback_query, fake_bot):
        wire(callback_query_handler, prodcast_message, send_events)
        callback_query_handler.session.add(User(id=1, chat_id=100, username="alice"))
        callback_query_handler.session.commit()

        callback_query_handler.handle_callback_query(
            make_callback_query(f"{CallbackData.CONSENT.value};decline")
        )

        assert callback_query_handler.session.get(User, 1).consent_given is False

    def test_accept_without_username_uses_first_name(
        self, wire, make_callback_query, fake_bot
    ):
        wire(callback_query_handler, prodcast_message, send_events)
        callback_query_handler.session.add_all([
            User(id=1, chat_id=100, username=None),
            User(id=99, chat_id=999, is_admin=True),
        ])
        callback_query_handler.session.commit()

        callback_query_handler.handle_callback_query(
            make_callback_query(
                f"{CallbackData.CONSENT.value};accept",
                user_id=1,
                username=None,
                first_name="Alice",
                last_name="Schmidt",
            )
        )

        texts = [
            call.kwargs.get("text", "") for call in fake_bot.send_message.call_args_list
        ]
        assert "Alice Schmidt tritt der Gang bei" in texts
        assert not any("@None" in text for text in texts)
