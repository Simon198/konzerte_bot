"""Unit tests for the consent/datenschutz helpers in ``telegram.consent``."""

from telegram.callback_data import CallbackData
from telegram.consent import (
    ACCEPT,
    DECLINE,
    DATENSCHUTZ_URL,
    get_consent_keyboard,
    get_consent_text,
    get_datenschutz_keyboard,
)


def test_consent_text_mentions_dataschutz():
    text = get_consent_text()
    assert "konzert_bot" in text
    # The consent text links the public repository (not the privacy-policy file
    # URL that is attached to the buttons).
    assert "https://github.com/Simon198/konzerte_bot/" in text
    assert "Datenschutzerklärung" in text


def test_consent_keyboard_structure():
    markup = get_consent_keyboard()
    rows = markup.keyboard

    # First row: a single link button to the privacy policy.
    assert rows[0][0].text == "Datenschutzerklärung"
    assert rows[0][0].url == DATENSCHUTZ_URL

    # Second row: accept / decline buttons.
    assert rows[1][0].text == "Ich stimme zu"
    assert rows[1][0].callback_data == f"{CallbackData.CONSENT.value};{ACCEPT}"
    assert rows[1][1].text == "Ich lehne ab"
    assert rows[1][1].callback_data == f"{CallbackData.CONSENT.value};{DECLINE}"


def test_datenschutz_keyboard_structure():
    markup = get_datenschutz_keyboard()
    rows = markup.keyboard
    assert rows[0][0].text == "Datenschutzerklärung öffnen"
    assert rows[0][0].url == DATENSCHUTZ_URL
