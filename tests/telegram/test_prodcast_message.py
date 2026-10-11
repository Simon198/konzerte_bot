"""Unit tests for ``telegram.prodcast_message`` (message broadcasting)."""

from models.user import User
from telegram import prodcast_message


class TestLoadAdmins:
    def test_returns_only_admins(self, session, monkeypatch):
        monkeypatch.setattr(prodcast_message, "session", session)
        admin = User(id=1, chat_id=100, is_admin=True)
        regular = User(id=2, chat_id=200, is_admin=False)
        session.add_all([admin, regular])
        session.commit()

        assert list(prodcast_message._load_admins(None)) == [admin]

    def test_excludes_given_user_id(self, session, monkeypatch):
        monkeypatch.setattr(prodcast_message, "session", session)
        admin_1 = User(id=1, chat_id=100, is_admin=True)
        admin_2 = User(id=2, chat_id=200, is_admin=True)
        session.add_all([admin_1, admin_2])
        session.commit()

        assert list(prodcast_message._load_admins(1)) == [admin_2]


class TestProdcastToAdmins:
    def test_sends_only_to_admins(self, session, monkeypatch, fake_bot):
        monkeypatch.setattr(prodcast_message, "session", session)
        monkeypatch.setattr(prodcast_message, "telegram_bot", fake_bot)
        admin = User(id=1, chat_id=100, is_admin=True)
        regular = User(id=2, chat_id=200, is_admin=False)
        session.add_all([admin, regular])
        session.commit()

        prodcast_message.prodcast_message_to_admins("hello")

        fake_bot.send_message.assert_called_once_with(chat_id=100, text="hello")


class TestProdcastToAll:
    def test_sends_to_every_user(self, session, monkeypatch, fake_bot):
        monkeypatch.setattr(prodcast_message, "session", session)
        monkeypatch.setattr(prodcast_message, "telegram_bot", fake_bot)
        session.add_all([User(id=1, chat_id=100), User(id=2, chat_id=200)])
        session.commit()

        prodcast_message.prodcast_message_to_all("hello", parse_mode="HTML")

        assert fake_bot.send_message.call_count == 2
