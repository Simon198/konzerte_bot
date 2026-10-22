import json
from io import BytesIO

from telebot.types import InputFile

from models.user import User
from utils import format_user_name

from . import telegram_bot


def _event_fields(event) -> dict:
    """Return readable event fields, tolerating orphaned references (event == None)."""
    if event is None:
        return {"band": None, "city": None, "location": None, "event_date": None}
    return {
        "band": event.band_name,
        "city": event.city,
        "location": event.location,
        "event_date": event.event_date.isoformat() if event.event_date else None,
    }


def build_user_data(user: User) -> dict:
    """Assemble all personal data stored for a user (Art. 15 / Art. 20 DSGVO)."""
    return {
        "user": {
            "id": user.id,
            "chat_id": user.chat_id,
            "username": user.username,
            "is_admin": user.is_admin,
            "consent_given": user.consent_given,
            "consent_date": user.consent_date.isoformat() if user.consent_date else None,
            "consent_version": user.consent_version,
        },
        "interests": [
            {
                "event_id": str(interest.event.id)
                if interest.event is not None
                else str(interest.event_id),
                **_event_fields(interest.event),
            }
            for interest in user.interest
        ],
        "observed_events": [
            {
                "event_id": str(observed.event.id)
                if observed.event is not None
                else str(observed.event_id),
                "band": observed.event.band_name if observed.event is not None else None,
                "message_id": observed.message_id,
            }
            for observed in user.observed
        ],
        "source_unsubscriptions": [
            unsubscription.source.value for unsubscription in user.source_unsubscriptions
        ],
        "genre_unsubscriptions": [
            unsubscription.genre.name
            if unsubscription.genre is not None
            else str(unsubscription.genre_id)
            for unsubscription in user.genre_unsubscriptions
        ],
    }


def _build_summary(user: User) -> str:
    username = format_user_name(username=user.username)
    if user.consent_given and user.consent_date:
        consent = f"erteilt (am {user.consent_date.strftime('%d.%m.%Y %H:%M')})"
    else:
        consent = "nicht erteilt"

    lines = [
        "Auskunft über deine gespeicherten Daten (Art. 15 DSGVO):",
        "",
        f"Nutzer-ID: {user.id}",
        f"Chat-ID: {user.chat_id}",
        f"Benutzername: {username}",
        f"Admin: {'ja' if user.is_admin else 'nein'}",
        f"Einwilligung: {consent}",
        "",
    ]

    if user.interest:
        lines.append("Interessierte Konzerte:")
        for interest in user.interest:
            if interest.event is not None:
                lines.append(f"  • {interest.event.get_short_message_text()}")
            else:
                lines.append(f"  • (Konzert nicht mehr verfügbar, ID {interest.event_id})")
        lines.append("")

    if user.source_unsubscriptions:
        lines.append("Abbestellte Quellen:")
        for unsubscription in user.source_unsubscriptions:
            lines.append(f"  • {unsubscription.source.value}")
        lines.append("")

    if user.genre_unsubscriptions:
        lines.append("Abgewählte Genres:")
        for unsubscription in user.genre_unsubscriptions:
            name = (
                unsubscription.genre.name
                if unsubscription.genre is not None
                else str(unsubscription.genre_id)
            )
            lines.append(f"  • {name}")
        lines.append("")

    lines.append(f"Bereits angezeigte Konzerte: {len(user.observed)}")
    lines.append(
        "Die vollständigen Daten erhältst du zusätzlich als maschinenlesbare "
        "JSON-Datei (Art. 20 DSGVO)."
    )

    return "\n".join(lines)


def _build_json_bytes(user: User) -> bytes:
    """Serialize the user's data to pretty-printed JSON bytes (pure)."""
    return json.dumps(build_user_data(user), ensure_ascii=False, indent=2).encode("utf-8")


def send_user_data(user: User) -> None:  # pragma: no cover - Telegram I/O
    """Send a readable summary (Art. 15) and a machine-readable JSON (Art. 20)."""
    summary = _build_summary(user)
    json_bytes = _build_json_bytes(user)

    telegram_bot.send_message(chat_id=user.chat_id, text=summary)
    telegram_bot.send_document(
        chat_id=user.chat_id,
        document=InputFile(BytesIO(json_bytes), file_name="konzert_bot_daten.json"),
        caption="Deine Daten als maschinenlesbare JSON-Datei.",
    )
