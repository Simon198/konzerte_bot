"""Integration tests for the command handlers in ``telegram.message_handler``."""

import types
from datetime import date, datetime

import pytest
from sqlalchemy import select

from models.changelog import Changelog
from models.band import Band
from models.event import Event, Source
from models.feature import Feature
from models.poll import Poll
from models.user import Interest, User
from telegram import message_handler, mydata, send_events

pytestmark = pytest.mark.integration


class TestStart:
    def test_new_user_gets_consent_message(self, wire, make_message, fake_bot):
        wire(message_handler)
        message_handler.start(make_message(user_id=1, chat_id=100, username="alice"))

        user = message_handler.session.get(User, 1)
        assert user is not None
        assert user.chat_id == 100
        assert user.username == "alice"
        fake_bot.send_message.assert_called_once()
        assert "konzert_bot" in fake_bot.send_message.call_args.kwargs["text"]

    def test_existing_user_with_consent_gets_welcome(self, wire, make_message, fake_bot):
        wire(message_handler, send_events)
        message_handler.session.add(
            User(id=1, chat_id=100, username="alice", consent_given=True)
        )
        message_handler.session.commit()

        message_handler.start(make_message(user_id=1, chat_id=100))

        fake_bot.send_message.assert_called_once()
        assert "Willkommen" in fake_bot.send_message.call_args.kwargs["text"]

    def test_admin_gets_hoheit_greeting(self, wire, make_message, fake_bot):
        wire(message_handler, send_events)
        message_handler.session.add(
            User(id=1, chat_id=100, username="alice", consent_given=True, is_admin=True)
        )
        message_handler.session.commit()

        message_handler.start(make_message(user_id=1, chat_id=100))

        assert "meine Hoheit" in fake_bot.send_message.call_args.kwargs["text"]


class TestFeature:
    def test_stores_feature_request(self, wire, make_message, fake_bot):
        wire(message_handler)
        message_handler.session.add(User(id=1, chat_id=100))
        message_handler.session.commit()

        message_handler.feature(make_message(user_id=1, text="/feature Mehr Metal"))

        features = message_handler.session.scalars(select(Feature)).all()
        assert len(features) == 1
        assert features[0].text == "Mehr Metal"
        fake_bot.reply_to.assert_called_once()


class TestDeleteUser:
    def test_deletes_user(self, wire, make_message, fake_bot):
        wire(message_handler)
        message_handler.session.add(User(id=1, chat_id=100))
        message_handler.session.commit()

        message_handler.delete_user(make_message(user_id=1, chat_id=100))

        assert message_handler.session.get(User, 1) is None
        fake_bot.send_message.assert_called_once()


class TestNextInterestedEvents:
    def test_sends_interested_event(self, wire, make_message, fake_bot):
        wire(message_handler)
        event = Event(
            dto_id="1", source=Source.BATSCHKAPP, band=Band(name="Band A"), city="F",
            location="L", event_date=date(2026, 6, 1),
        )
        user = User(id=1, chat_id=100)
        user.interest.append(Interest(event=event))
        message_handler.session.add(user)
        message_handler.session.commit()

        message_handler.next_interested_events(
            make_message(user_id=1, chat_id=100, text="/next")
        )

        fake_bot.send_message.assert_called_once()
        assert "Band A" in fake_bot.send_message.call_args.kwargs["text"]


class TestGo:
    def test_sends_next_event(self, wire, make_message, fake_bot):
        wire(message_handler, send_events)
        message_handler.session.add(User(id=1, chat_id=100, consent_given=True))
        message_handler.session.add(
            Event(
                dto_id="1", source=Source.BATSCHKAPP, band=Band(name="Band A"), city="F",
                location="L", event_date=date(2026, 6, 1),
            )
        )
        message_handler.session.commit()
        fake_bot.send_message.side_effect = lambda **kw: types.SimpleNamespace(id=1)

        message_handler.go(make_message(user_id=1, chat_id=100, text="/go"))

        fake_bot.send_message.assert_called()


class TestSources:
    def test_creates_poll_from_distinct_sources(self, wire, make_message, fake_bot):
        wire(message_handler)
        message_handler.session.add_all([
            Event(dto_id="1", source=Source.BATSCHKAPP, band=Band(name="A"), city="F", location="L", event_date=date(2026, 6, 1)),
            Event(dto_id="2", source=Source.FESTHALLE, band=Band(name="B"), city="F", location="L", event_date=date(2026, 6, 1)),
        ])
        message_handler.session.commit()

        def fake_send_poll(**kwargs):
            options = kwargs["options"]
            poll = types.SimpleNamespace(
                id=123, options=[types.SimpleNamespace(text=t) for t in options]
            )
            return types.SimpleNamespace(poll=poll)

        fake_bot.send_poll.side_effect = fake_send_poll

        message_handler.sources(make_message(chat_id=100))

        poll = message_handler.session.get(Poll, 123)
        assert poll is not None
        assert {o.source for o in poll.poll_options} == {Source.BATSCHKAPP, Source.FESTHALLE}


class TestPairings:
    def test_lists_shared_interests(self, wire, make_message, fake_bot):
        wire(message_handler)
        admin = User(id=1, chat_id=100, username="admin", is_admin=True)
        other = User(id=2, chat_id=200, username="bob")
        event = Event(
            dto_id="1", source=Source.BATSCHKAPP, band=Band(name="Metallica"), city="F",
            location="L", event_date=date(2026, 6, 1),
        )
        admin.interest.append(Interest(event=event))
        other.interest.append(Interest(event=event))
        message_handler.session.add_all([admin, other])
        message_handler.session.commit()

        message_handler.pairings(make_message(user_id=1, chat_id=100))

        text = fake_bot.send_message.call_args.kwargs["text"]
        assert "Metallica" in text
        assert "@bob" in text


class TestChangelog:
    def test_sends_latest_changelog(
        self, wire, make_message, fake_bot, tmp_path, monkeypatch
    ):
        import send_changelog

        wire(message_handler)
        changelog_file = tmp_path / "CHANGELOG_0.1.md"
        changelog_file.write_text("# Version 0.1\n", encoding="utf-8")
        monkeypatch.setattr(send_changelog, "CHANGELOG_FOLDER", str(tmp_path))

        message_handler.session.add(
            Changelog(file_name="CHANGELOG_0.1.md", sent_date=datetime.now())
        )
        message_handler.session.commit()

        message_handler.changelog(make_message(chat_id=100))

        fake_bot.reply_to.assert_called_once()
        assert "<b>Version 0.1</b>" in fake_bot.reply_to.call_args.kwargs["text"]


class TestMydata:
    def test_sends_user_data(self, wire, make_message, fake_bot):
        wire(message_handler, mydata)
        message_handler.session.add(
            User(id=1, chat_id=100, username="alice", consent_given=True)
        )
        message_handler.session.commit()

        message_handler.mydata(make_message(user_id=1, chat_id=100))

        fake_bot.send_message.assert_called_once()
        fake_bot.send_document.assert_called_once()


class TestSetupBotCommands:
    def test_registers_commands(self, wire, fake_bot):
        wire(message_handler)
        message_handler.setup_bot_commands()
        fake_bot.set_my_commands.assert_called_once()
