from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from .callback_data import CallbackData

GENRE_FILTER_TEXT = (
    "Tippe auf ein Genre, um es zu blockieren. "
    "Blockierte Genres sind mit ❌ markiert. "
    "Tippe erneut auf ein blockiertes Genre, um es wieder freizugeben."
)


def build_genre_keyboard(genres, disliked_genre_ids) -> InlineKeyboardMarkup:
    """Build the toggle keyboard listing every genre (pure).

    Genres the user already dislikes are prefixed with ``❌`` so the current
    state is visible at a glance. The trailing button closes the keyboard.
    """
    markup = InlineKeyboardMarkup()
    disliked = set(disliked_genre_ids)

    for genre in genres:
        label = f"❌ {genre.name}" if genre.id in disliked else genre.name
        markup.add(
            InlineKeyboardButton(
                text=label,
                callback_data=f"{CallbackData.GENRE.value};{genre.id}",
            )
        )

    markup.add(
        InlineKeyboardButton(
            text="✅ Fertig",
            callback_data=f"{CallbackData.GENRE_DONE.value};done",
        )
    )
    return markup
