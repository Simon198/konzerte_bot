"""Unit tests for ``telegram.callback_data``."""

from telegram.callback_data import CallbackData


def test_callback_data_values():
    assert CallbackData.INTERESTED.value == "interested"
    assert CallbackData.NOT_INTERESTED.value == "not_interested"
    assert CallbackData.CONSENT.value == "consent"
    assert CallbackData.GENRE.value == "genre"
    assert CallbackData.GENRE_DONE.value == "genre_done"
