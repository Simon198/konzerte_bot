import io
import logging
from dataclasses import dataclass
from pathlib import Path

import deezer
import requests
from PIL import Image

logger = logging.getLogger(__name__)

# Deezer picture sizes ordered by preference. ``picture_big`` (500x500 px) is a
# good-quality source that is then converted to a WebP sticker.
PICTURE_FIELDS = (
    "picture_big",
    "picture_medium",
    "picture_small",
    "picture",
    "picture_xl",
)

# Where downloaded band images are stored (relative to the project root).
HOME_FOLDER = Path(__file__).resolve().parent.parent
BAND_IMAGES_DIR = HOME_FOLDER / "images" / "bands"

# Telegram static stickers must be 512x512 px (one side exactly 512). Band
# images are downloaded and converted to a WebP sticker of this size.
STICKER_SIZE = 512

# Timeout (seconds) for a single Deezer search or image download, so a hanging
# network call does not stall the whole daily load.
REQUEST_TIMEOUT = 10


@dataclass
class BandInfo:
    """Deezer information derived for a single band.

    ``audio_sample`` and ``image_url`` are ``None`` when they could not be
    found. ``genres`` is ``None`` when the lookup failed (retry on the next
    load) and a (possibly empty) list when the lookup succeeded.
    """

    audio_sample: str | None = None
    image_url: str | None = None
    genres: list[str] | None = None


def _first_picture_url(artist: dict) -> str | None:
    """Return the first available picture URL in preference order (pure)."""
    for field in PICTURE_FIELDS:
        url = (artist or {}).get(field)
        if url:
            return url
    return None


def _first_top_track_link(top_tracks: list[dict]) -> str | None:
    """Return the Deezer link of the first top track (pure)."""
    if not top_tracks:
        return None
    return (top_tracks[0] or {}).get("link")


def _newest_album_id(albums: list[dict]) -> int | None:
    """Return the id of the newest album by ``release_date`` (pure).

    Deezer does not sort an artist's albums by release date, so the newest one
    has to be picked here. Albums without a usable ``release_date`` are skipped.
    """
    newest = None
    for album in albums:
        release_date = (album or {}).get("release_date")
        if not release_date:
            continue
        if newest is None or release_date > newest["release_date"]:
            newest = album
    return newest["id"] if newest else None


def _genre_names(album: dict) -> list[str]:
    """Return the genre names of a Deezer album (pure, de-duplicated)."""
    genres = (album or {}).get("genres") or []
    names = []
    for genre in genres:
        name = genre.get("name") if isinstance(genre, dict) else None
        if name and name not in names:
            names.append(name)
    return names


def find_band_information(band_name: str) -> BandInfo:  # pragma: no cover - network I/O
    """Search Deezer for ``band_name`` once and derive its information.

    The artist is looked up only once and shared across the audio sample, image
    and genre lookups. On any error the returned :class:`BandInfo` is left
    empty so nothing is filled and the band is retried on the next load.
    """
    try:
        with deezer.Client() as client:
            artists = client.search_artists(band_name)
            if not artists:
                return BandInfo()
            artist = artists[0]

            info = BandInfo()
            info.image_url = _first_picture_url(artist.as_dict())
            info.audio_sample = _first_top_track_link(
                [track.as_dict() for track in artist.get_top()[:1]]
            )
            album_id = _newest_album_id(
                [album.as_dict() for album in artist.get_albums()]
            )
            info.genres = (
                _genre_names(client.get_album(album_id).as_dict())
                if album_id is not None
                else []
            )
            return info
    except Exception:
        logger.exception("Could not find Deezer information for band %r", band_name)
        return BandInfo()


def _to_sticker_bytes(image_bytes: bytes) -> bytes:
    """Return ``image_bytes`` resized and converted to a WebP sticker (pure)."""
    with Image.open(io.BytesIO(image_bytes)) as image:
        image = image.convert("RGB").resize((STICKER_SIZE, STICKER_SIZE), Image.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, format="WEBP")
        return buffer.getvalue()


def download_band_image(url: str, file_name: str) -> str | None:  # pragma: no cover - network I/O
    """Download ``url``, convert it to a WebP sticker and store it.

    Returns the path of the stored image, or ``None`` if the download fails so
    callers can leave the band's ``image_path`` unset and retry on the next load.
    """
    BAND_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    destination = BAND_IMAGES_DIR / file_name
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        destination.write_bytes(_to_sticker_bytes(response.content))
        return str(destination)
    except Exception:
        logger.exception("Could not download band image from %r", url)
        return None
