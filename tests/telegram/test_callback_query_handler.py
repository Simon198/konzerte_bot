"""Unit tests for ``telegram.callback_query_handler``."""

from datetime import date
from unittest.mock import MagicMock

from models.event import Event, Source
from models.user import Interest, User
from telegram import callback_query_handler
from telegram.callback_data import CallbackData


def _patch_dependencies(monkeypatch, session, fake_bot):
    monkeypatch.setattr(callback_query_handler, "session", session)
    monkeypatch.setattr(callback_query_handler, "telegram_bot", fake_bot)
    monkeypatch.setattr(callback_query_handler, "prodcast_message_to_admins", MagicMock())
    monkeypatch.setattr(callback_query_handler, "send_events_to_user", MagicMock())


class TestInterested:
    def test_adds_interest(self, session, monkeypatch, make_callback_query, fake_bot):
        _patch_dependencies(monkeypatch, session, fake_bot)

        event = Event(
            dto_id="1", source=Source.BATSCHKAPP, band="Band A", city="F",
            location="L", event_date=date(2026, 6, 1),
        )
        session.add(User(id=1, chat_id=100, username="alice", consent_given=True))
        session.add(event)
        session.commit()

        callback_query_handler.handle_callback_query(
            make_callback_query(f"{CallbackData.INTERESTED.value};{event.id}")
        )

        session.expire_all()
        user = session.get(User, 1)
        assert len(user.interest) == 1
        assert user.interest[0].event_id == event.id
        callback_query_handler.prodcast_message_to_admins.assert_called_once()
        callback_query_handler.send_events_to_user.assert_called_once()
        fake_bot.edit_message_reply_markup.assert_called_once()


class TestNotInterested:
    def test_removes_interest(
        self, session, monkeypatch, make_callback_query, fake_bot
    ):
        _patch_dependencies(monkeypatch, session, fake_bot)

        event = Event(
            dto_id="1", source=Source.BATSCHKAPP, band="Band A", city="F",
            location="L", event_date=date(2026, 6, 1),
        )
        user = User(id=1, chat_id=100, username="alice", consent_given=True)
        user.interest.append(Interest(event=event))
        session.add(user)
        session.commit()

        callback_query_handler.handle_callback_query(
            make_callback_query(f"{CallbackData.NOT_INTERESTED.value};{event.id}")
        )

        session.expire_all()
        assert session.get(User, 1).interest == []


class TestConsent:
    def test_accept_marks_consent(
        self, session, monkeypatch, make_callback_query, fake_bot
    ):
        _patch_dependencies(monkeypatch, session, fake_bot)
        session.add(User(id=1, chat_id=100, username="alice"))
        session.commit()

        callback_query_handler.handle_callback_query(
            make_callback_query(f"{CallbackData.CONSENT.value};accept")
        )

        session.expire_all()
        user = session.get(User, 1)
        assert user.consent_given is True
        assert user.consent_version is not None
        fake_bot.send_message.assert_called_once()
        assert "Willkommen" in fake_bot.send_message.call_args.kwargs["text"]

    def test_decline_sends_explanation(
        self, session, monkeypatch, make_callback_query, fake_bot
    ):
        _patch_dependencies(monkeypatch, session, fake_bot)
        session.add(User(id=1, chat_id=100, username="alice"))
        session.commit()

        callback_query_handler.handle_callback_query(
            make_callback_query(f"{CallbackData.CONSENT.value};decline")
        )

        fake_bot.send_message.assert_called_once()
        assert "Ohne deine Einwilligung" in fake_bot.send_message.call_args.kwargs["text"]
