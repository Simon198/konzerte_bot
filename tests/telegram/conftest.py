"""Shared fixtures for the ``telegram`` package tests."""

import types
from unittest.mock import MagicMock

import pytest


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
def fake_bot():
    """A mock ``telebot.TeleBot`` used to replace ``telegram_bot`` in handlers."""
    return MagicMock()
