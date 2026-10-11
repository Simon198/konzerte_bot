"""Unit tests for the command handlers in ``telegram.message_handler``."""

from datetime import date
from unittest.mock import MagicMock

from sqlalchemy import select

from models.event import Event, Source
from models.feature import Feature
from models.user import Interest, User
from telegram import message_handler
from telegram.command import Commands


class TestStart:
    def test_new_user_is_created_and_asked_for_consent(
        self, session, monkeypatch, make_message, fake_bot
    ):
        monkeypatch.setattr(message_handler, "session", session)
        monkeypatch.setattr(message_handler, "telegram_bot", fake_bot)

        message_handler.start(make_message(user_id=1, chat_id=100, username="alice"))

        user = session.get(User, 1)
        assert user is not None
        assert user.chat_id == 100
        assert user.username == "alice"
        fake_bot.send_message.assert_called_once()
        assert "konzert_bot" in fake_bot.send_message.call_args.kwargs["text"]

    def test_existing_user_with_consent_gets_welcome(
        self, session, monkeypatch, make_message, fake_bot
    ):
        monkeypatch.setattr(message_handler, "session", session)
        monkeypatch.setattr(message_handler, "telegram_bot", fake_bot)
        monkeypatch.setattr(message_handler, "send_events_to_user", MagicMock())

        session.add(User(id=1, chat_id=100, username="alice", consent_given=True))
        session.commit()

        message_handler.start(
            make_message(user_id=1, chat_id=200, username="alice")
        )

        session.expire_all()
        assert session.get(User, 1).chat_id == 200
        fake_bot.send_message.assert_called_once()
        assert "Willkommen" in fake_bot.send_message.call_args.kwargs["text"]
        message_handler.send_events_to_user.assert_called_once()

    def test_admin_gets_hoheit_greeting(
        self, session, monkeypatch, make_message, fake_bot
    ):
        monkeypatch.setattr(message_handler, "session", session)
        monkeypatch.setattr(message_handler, "telegram_bot", fake_bot)
        monkeypatch.setattr(message_handler, "send_events_to_user", MagicMock())

        session.add(
            User(id=1, chat_id=100, username="alice", consent_given=True, is_admin=True)
        )
        session.commit()

        message_handler.start(make_message(user_id=1, chat_id=100))

        assert "meine Hoheit" in fake_bot.send_message.call_args.kwargs["text"]


class TestFeature:
    def test_stores_feature_request(
        self, session, monkeypatch, make_message, fake_bot
    ):
        monkeypatch.setattr(message_handler, "session", session)
        monkeypatch.setattr(message_handler, "telegram_bot", fake_bot)
        session.add(User(id=1, chat_id=100))
        session.commit()

        message_handler.feature(make_message(user_id=1, text="/feature Mehr Metal"))

        features = session.scalars(select(Feature)).all()
        assert len(features) == 1
        assert features[0].text == "Mehr Metal"
        fake_bot.reply_to.assert_called_once()

    def test_empty_feature_is_rejected(
        self, session, monkeypatch, make_message, fake_bot
    ):
        monkeypatch.setattr(message_handler, "session", session)
        monkeypatch.setattr(message_handler, "telegram_bot", fake_bot)
        session.add(User(id=1, chat_id=100))
        session.commit()

        message_handler.feature(make_message(user_id=1, text="/feature"))

        fake_bot.reply_to.assert_called_once()
        assert session.scalars(select(Feature)).all() == []


class TestNextInterestedEvents:
    def test_sends_interested_event(
        self, session, monkeypatch, make_message, fake_bot
    ):
        monkeypatch.setattr(message_handler, "session", session)
        monkeypatch.setattr(message_handler, "telegram_bot", fake_bot)

        event = Event(
            dto_id="1", source=Source.BATSCHKAPP, band="Band A", city="F",
            location="L", event_date=date(2026, 6, 1),
        )
        user = User(id=1, chat_id=100)
        user.interest.append(Interest(event=event))
        session.add(user)
        session.commit()

        message_handler.next_interested_events(
            make_message(user_id=1, chat_id=100, text="/next")
        )

        fake_bot.send_message.assert_called_once()
        assert "Band A" in fake_bot.send_message.call_args.kwargs["text"]

    def test_no_interests_returns_info(
        self, session, monkeypatch, make_message, fake_bot
    ):
        monkeypatch.setattr(message_handler, "session", session)
        monkeypatch.setattr(message_handler, "telegram_bot", fake_bot)
        session.add(User(id=1, chat_id=100))
        session.commit()

        message_handler.next_interested_events(
            make_message(user_id=1, chat_id=100, text="/next")
        )

        fake_bot.send_message.assert_called_once()
        assert "keine anstehenden Konzerte" in fake_bot.send_message.call_args.kwargs["text"]


class TestDeleteUser:
    def test_deletes_registered_user(
        self, session, monkeypatch, make_message, fake_bot
    ):
        monkeypatch.setattr(message_handler, "session", session)
        monkeypatch.setattr(message_handler, "telegram_bot", fake_bot)
        session.add(User(id=1, chat_id=100))
        session.commit()

        message_handler.delete_user(make_message(user_id=1, chat_id=100))

        assert session.get(User, 1) is None
        fake_bot.send_message.assert_called_once()

    def test_unregistered_user_gets_notice(
        self, session, monkeypatch, make_message, fake_bot
    ):
        monkeypatch.setattr(message_handler, "session", session)
        monkeypatch.setattr(message_handler, "telegram_bot", fake_bot)

        message_handler.delete_user(make_message(user_id=99, chat_id=100))

        fake_bot.send_message.assert_called_once()
        assert "nicht registriert" in fake_bot.send_message.call_args.kwargs["text"]


class TestPairings:
    def test_non_admin_is_denied(
        self, session, monkeypatch, make_message, fake_bot
    ):
        monkeypatch.setattr(message_handler, "session", session)
        monkeypatch.setattr(message_handler, "telegram_bot", fake_bot)
        session.add(User(id=1, chat_id=100, is_admin=False))
        session.commit()

        message_handler.pairings(make_message(user_id=1, chat_id=100))

        fake_bot.reply_to.assert_called_once()
        assert "keine Berechtigung" in fake_bot.reply_to.call_args.kwargs["text"]

    def test_lists_events_shared_with_other_users(
        self, session, monkeypatch, make_message, fake_bot
    ):
        monkeypatch.setattr(message_handler, "session", session)
        monkeypatch.setattr(message_handler, "telegram_bot", fake_bot)

        admin = User(id=1, chat_id=100, username="admin", is_admin=True)
        other = User(id=2, chat_id=200, username="bob")
        event = Event(
            dto_id="1", source=Source.BATSCHKAPP, band="Metallica", city="F",
            location="L", event_date=date(2026, 6, 1),
        )
        admin.interest.append(Interest(event=event))
        other.interest.append(Interest(event=event))
        session.add_all([admin, other])
        session.commit()

        message_handler.pairings(make_message(user_id=1, chat_id=100))

        text = fake_bot.send_message.call_args.kwargs["text"]
        assert "Metallica" in text
        assert "@bob" in text


class TestSetupBotCommands:
    def test_registers_one_command_per_enum_member(self, monkeypatch, fake_bot):
        monkeypatch.setattr(message_handler, "telegram_bot", fake_bot)

        message_handler.setup_bot_commands()

        fake_bot.set_my_commands.assert_called_once()
        commands = fake_bot.set_my_commands.call_args.args[0]
        assert len(commands) == len(Commands)
