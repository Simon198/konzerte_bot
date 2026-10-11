"""Unit tests for ``telegram.poll_answer_handler``."""

from models.event import Source
from models.poll import PollOption
from telegram import poll_answer_handler


def _poll_options():
    return [PollOption(id=i, source=source) for i, source in enumerate(Source)]


class TestSourcesToUnsubscribe:
    def test_returns_unselected_sources(self):
        assert poll_answer_handler._sources_to_unsubscribe(
            _poll_options(), [0, 1]
        ) == {Source.JAHRHUNDERTHALLE, Source.SCHLACHTHOF}

    def test_all_selected_returns_empty(self):
        assert poll_answer_handler._sources_to_unsubscribe(
            _poll_options(), [0, 1, 2, 3]
        ) == set()

    def test_none_selected_returns_all(self):
        assert poll_answer_handler._sources_to_unsubscribe(
            _poll_options(), []
        ) == set(Source)
