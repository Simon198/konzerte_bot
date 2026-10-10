from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from .callback_data import CallbackData

DATENSCHUTZ_URL = "https://github.com/Simon198/konzerte_bot/blob/main/DATENSCHUTZ.md"
DATENSCHUTZ_VERSION = "2026-10-10"

ACCEPT = "accept"
DECLINE = "decline"


def get_consent_text() -> str:
    return (
        "Willkommen bei konzert_bot!\n\n"
        "Ich informiere dich über Konzerte und merke mir dafür deine Einstellungen. "
        "Damit ich dir Nachrichten schicken darf, verarbeitet Telegram deine Daten auch "
        "auf Servern außerhalb der EU (u. a. in den USA). Außerdem informiere ich den "
        "Administrator über neue Nutzer und deine markierten Interessen.\n\n"
        "Der Quellcode ist öffentlich auf GitHub verfügbar: "
        "https://github.com/Simon198/konzerte_bot/\n\n"
        "Bitte lies die Datenschutzerklärung und bestätige mit „Ich stimme zu“."
    )


def get_consent_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Datenschutzerklärung", url=DATENSCHUTZ_URL))
    markup.row(
        InlineKeyboardButton(
            text="Ich stimme zu",
            callback_data=f"{CallbackData.CONSENT.value};{ACCEPT}",
        ),
        InlineKeyboardButton(
            text="Ich lehne ab",
            callback_data=f"{CallbackData.CONSENT.value};{DECLINE}",
        ),
    )
    return markup


def get_datenschutz_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Datenschutzerklärung öffnen", url=DATENSCHUTZ_URL))
    return markup
