import logging

logger = logging.getLogger(__name__)

# Timeout (seconds) for a single YouTube search, so a hanging network call does
# not stall the whole daily load.
SEARCH_TIMEOUT = 10


def _first_result_link(result: dict) -> str | None:
    """Return the watch URL of the first search result (pure)."""
    items = (result or {}).get("result") or []
    if not items:
        return None
    return items[0].get("link")


def find_audio_sample(band_name: str) -> str | None:  # pragma: no cover - network I/O
    """Find a YouTube link for ``band_name``, or ``None`` if none was found."""
    try:
        from youtubesearchpython import VideosSearch

        search = VideosSearch(band_name + " Band", limit=1, timeout=SEARCH_TIMEOUT)
        return _first_result_link(search.result())
    except Exception:
        logger.exception("Could not find an audio sample for band %r", band_name)
        return None
