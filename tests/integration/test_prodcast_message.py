"""Integration tests for ``telegram.prodcast_message``."""

import pytest

from models.user import User
from telegram import prodcast_message

pytestmark = pytest.mark.integration


class TestProdcastMessageToAdmins:
    def test_sends_only_to_admins(self, wire, fake_bot):
        wire(prodcast_message)
        prodcast_message.session.add_all([
            User(id=1, chat_id=100, is_admin=True),
            User(id=2, chat_id=200, is_admin=False),
        ])
        prodcast_message.session.commit()

        prodcast_message.prodcast_message_to_admins("hello")

        fake_bot.send_message.assert_called_once_with(chat_id=100, text="hello")


class TestProdcastMessageToAll:
    def test_sends_to_every_user(self, wire, fake_bot):
        wire(prodcast_message)
        prodcast_message.session.add_all([
            User(id=1, chat_id=100),
            User(id=2, chat_id=200),
        ])
        prodcast_message.session.commit()

        prodcast_message.prodcast_message_to_all("hello")

        assert fake_bot.send_message.call_count == 2
