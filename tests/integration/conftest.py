"""Shared fixtures for integration tests.

Integration tests exercise the database-storage and Telegram I/O code that is
excluded from the unit tests (the functions marked ``# pragma: no cover``).
They use a real in-memory SQLite database and a fake Telegram bot (the external
API boundary).
"""

import types
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from models import Base


@pytest.fixture
def session():
    """A fresh in-memory SQLite session with the full schema."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db_session = Session(engine)
    try:
        yield db_session
    finally:
        db_session.close()
        engine.dispose()


@pytest.fixture
def fake_bot():
    """A mock Telegram bot standing in for the external Telegram API."""
    bot = MagicMock()
    # A sent message needs a numeric ``.id`` (used when recording ``Observed``).
    bot.send_message.return_value = types.SimpleNamespace(id=1)
    return bot


@pytest.fixture
def make_message():
    """Factory returning a lightweight stand-in for ``telebot.types.Message``."""

    def _make(user_id=1, chat_id=100, username="alice", text="/start"):
        return types.SimpleNamespace(
            from_user=types.SimpleNamespace(id=user_id, username=username),
            chat=types.SimpleNamespace(id=chat_id),
            text=text,
        )

    return _make


@pytest.fixture
def make_callback_query():
    """Factory returning a lightweight stand-in for ``telebot.types.CallbackQuery``."""

    def _make(data, user_id=1, chat_id=100, message_id=555, username="alice"):
        return types.SimpleNamespace(
            data=data,
            from_user=types.SimpleNamespace(id=user_id, username=username),
            message=types.SimpleNamespace(id=message_id, chat=types.SimpleNamespace(id=chat_id)),
        )

    return _make


@pytest.fixture
def wire(monkeypatch, session, fake_bot):
    """Redirect the given modules' ``session`` and ``telegram_bot`` to the test DB/bot.

    The application imports ``session``/``telegram_bot`` as module-level globals
    (``from repository import session``), so each module under test must be
    pointed at the test database and the fake bot individually.
    """

    def _wire(*modules):
        for module in modules:
            # ``raising=False`` because not every module exposes ``telegram_bot``
            # (e.g. ``send_changelog`` delegates to ``prodcast_message``).
            monkeypatch.setattr(module, "session", session, raising=False)
            monkeypatch.setattr(module, "telegram_bot", fake_bot, raising=False)

    return _wire
