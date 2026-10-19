"""Integration tests for ``send_changelog``."""

from datetime import datetime

import pytest
from sqlalchemy import select

import send_changelog
from models.changelog import Changelog
from models.user import User
from telegram import prodcast_message

pytestmark = pytest.mark.integration


class TestProdcastNewestChangelog:
    def test_records_and_broadcasts(self, wire, fake_bot, tmp_path, monkeypatch):
        wire(send_changelog, prodcast_message)

        (tmp_path / "CHANGELOG_0.1.md").write_text("# Version 0.1\n", encoding="utf-8")
        monkeypatch.setattr(send_changelog, "CHANGELOG_FOLDER", str(tmp_path))

        prodcast_message.session.add(User(id=1, chat_id=100))
        prodcast_message.session.commit()

        send_changelog.prodcast_newest_changelog()

        changelogs = send_changelog.session.scalars(select(Changelog)).all()
        assert len(changelogs) == 1
        assert changelogs[0].file_name == "CHANGELOG_0.1.md"
        fake_bot.send_message.assert_called_once()

    def test_no_new_changelog_sends_nothing(self, wire, fake_bot, tmp_path, monkeypatch):
        wire(send_changelog, prodcast_message)

        monkeypatch.setattr(send_changelog, "CHANGELOG_FOLDER", str(tmp_path))
        (tmp_path / "CHANGELOG_0.1.md").write_text("# Version 0.1\n", encoding="utf-8")

        # Already tracked in the DB -> nothing new to broadcast.
        send_changelog.session.add(
            Changelog(file_name="CHANGELOG_0.1.md", sent_date=datetime.now())
        )
        prodcast_message.session.add(User(id=1, chat_id=100))
        prodcast_message.session.commit()

        send_changelog.prodcast_newest_changelog()

        fake_bot.send_message.assert_not_called()
