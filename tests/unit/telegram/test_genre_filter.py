"""Unit tests for ``telegram.genre_filter``."""

from models.genre import Genre
from telegram.callback_data import CallbackData
from telegram.genre_filter import build_genre_keyboard


def test_genre_keyboard_marks_disliked_genres():
    genres = [Genre(id=1, name="Rock"), Genre(id=2, name="Pop")]

    markup = build_genre_keyboard(genres, disliked_genre_ids={1})

    buttons = [row[0] for row in markup.keyboard]
    # 2 genre buttons + 1 done button
    assert len(buttons) == 3
    assert buttons[0].text == "❌ Rock"
    assert buttons[0].callback_data == f"{CallbackData.GENRE.value};1"
    assert buttons[1].text == "Pop"
    assert buttons[1].callback_data == f"{CallbackData.GENRE.value};2"


def test_genre_keyboard_appends_done_button():
    markup = build_genre_keyboard([Genre(id=1, name="Rock")], disliked_genre_ids=set())

    done_button = markup.keyboard[-1][0]
    assert done_button.text == "✅ Fertig"
    assert done_button.callback_data == f"{CallbackData.GENRE_DONE.value};done"


def test_genre_keyboard_empty_genres_only_done_button():
    markup = build_genre_keyboard([], disliked_genre_ids=set())

    assert len(markup.keyboard) == 1
    assert markup.keyboard[0][0].text == "✅ Fertig"
