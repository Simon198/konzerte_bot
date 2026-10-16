"""Unit tests for ``utils``."""

import pytest

from utils import format_user_name

pytestmark = pytest.mark.unit


class TestFormatUserName:
    def test_prefers_username(self):
        assert format_user_name(username="alice") == "@alice"

    def test_username_wins_over_name_and_id(self):
        assert (
            format_user_name(
                username="alice", first_name="Alice", last_name="Schmidt", user_id=1
            )
            == "@alice"
        )

    def test_falls_back_to_full_name(self):
        assert (
            format_user_name(username=None, first_name="Alice", last_name="Schmidt")
            == "Alice Schmidt"
        )

    def test_falls_back_to_first_name_only(self):
        assert format_user_name(username=None, first_name="Alice") == "Alice"

    def test_falls_back_to_user_id(self):
        assert format_user_name(username=None, user_id=2) == "Nutzer 2"

    def test_falls_back_to_none_when_nothing_known(self):
        assert format_user_name() == "(keiner)"

    def test_skips_empty_name_parts(self):
        assert (
            format_user_name(username=None, first_name="", last_name="Schmidt")
            == "Schmidt"
        )
