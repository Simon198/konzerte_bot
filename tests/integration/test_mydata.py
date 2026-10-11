"""Integration tests for ``telegram.mydata``."""

import pytest

from models.user import User
from telegram import mydata

pytestmark = pytest.mark.integration


class TestSendUserData:
    def test_sends_summary_and_document(self, wire, fake_bot):
        wire(mydata)
        user = User(id=1, chat_id=100, username="alice", consent_given=True)
        mydata.session.add(user)
        mydata.session.commit()

        mydata.send_user_data(user)

        fake_bot.send_message.assert_called_once()
        assert fake_bot.send_message.call_args.kwargs["chat_id"] == 100
        fake_bot.send_document.assert_called_once()
