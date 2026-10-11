"""Unit tests for ``telegram.callback_query_handler``."""

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
