TIMEZONE = "Europe/Berlin"


def format_user_name(
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    user_id: int | None = None,
) -> str:
    """Return a human-readable display name for a user (pure).

    Prefers the ``@username``, falls back to the first/last name, then to
    ``Nutzer <id>``, and finally to ``(keiner)`` when nothing is known. This is
    the single place that turns user identifiers into a display string so no
    caller ever renders ``@None`` for users without a Telegram username.
    """
    if username:
        return f"@{username}"
    name = " ".join(part for part in (first_name, last_name) if part)
    if name:
        return name
    if user_id is not None:
        return f"Nutzer {user_id}"
    return "(keiner)"
