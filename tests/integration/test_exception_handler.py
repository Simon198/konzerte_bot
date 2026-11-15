"""Integration tests for the Telegram bot exception handler in ``telegram``."""

from unittest.mock import MagicMock

import pytest

import telegram

pytestmark = pytest.mark.integration


class TestExceptionHandler:
    def test_handle_resets_scoped_session_and_marks_handled(self):
        # Uses the real scoped session (which has a ``remove`` method).
        handler = telegram._ExceptionHandler()

        assert handler.handle(RuntimeError("boom")) is True

    def test_handle_still_marks_handled_when_reset_fails(self, monkeypatch):
        import repository

        fake_session = MagicMock()
        fake_session.rollback.side_effect = RuntimeError("reset failed")
        monkeypatch.setattr(repository, "session", fake_session)

        handler = telegram._ExceptionHandler()

        assert handler.handle(RuntimeError("boom")) is True
