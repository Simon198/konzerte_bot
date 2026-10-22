"""Unit tests for ``telegram.callback_query_handler``."""

from models.user import GenreUnsubscription, User
from telegram import callback_query_handler


class TestParseCallbackData:
    def test_parses_action_and_value(self):
        assert callback_query_handler._parse_callback_data("interested;123") == (
            "interested",
            "123",
        )

    def test_returns_none_when_no_separator(self):
        assert callback_query_handler._parse_callback_data("no-semicolon") is None

    def test_returns_none_when_too_many_parts(self):
        assert callback_query_handler._parse_callback_data("a;b;c") is None


class TestToggleGenreUnsubscription:
    def test_adds_unsubscription_when_not_present(self):
        user = User(id=1, chat_id=100)
        callback_query_handler._toggle_genre_unsubscription(user, genre_id=5)

        assert [u.genre_id for u in user.genre_unsubscriptions] == [5]

    def test_removes_unsubscription_when_present(self):
        user = User(id=1, chat_id=100)
        user.genre_unsubscriptions.append(GenreUnsubscription(genre_id=5))

        callback_query_handler._toggle_genre_unsubscription(user, genre_id=5)

        assert user.genre_unsubscriptions == []
