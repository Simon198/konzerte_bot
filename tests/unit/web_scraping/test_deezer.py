"""Unit tests for the Deezer helpers in ``web_scraping.deezer``."""

import io

from PIL import Image

from web_scraping import deezer


class TestFirstPictureUrl:
    def test_prefers_picture_big(self):
        artist = {
            "picture_big": "https://cdn.example/big.jpg",
            "picture_xl": "https://cdn.example/xl.jpg",
        }
        assert deezer._first_picture_url(artist) == "https://cdn.example/big.jpg"

    def test_falls_back_when_picture_big_missing(self):
        artist = {
            "picture_medium": "https://cdn.example/medium.jpg",
            "picture_xl": "https://cdn.example/xl.jpg",
        }
        assert deezer._first_picture_url(artist) == "https://cdn.example/medium.jpg"

    def test_falls_back_to_smaller_sizes(self):
        artist = {"picture": "https://cdn.example/small.jpg"}
        assert deezer._first_picture_url(artist) == "https://cdn.example/small.jpg"

    def test_none_when_no_picture_fields(self):
        assert deezer._first_picture_url({"name": "No Image"}) is None

    def test_none_when_picture_is_empty_string(self):
        assert deezer._first_picture_url({"picture_big": ""}) is None

    def test_none_for_none_input(self):
        assert deezer._first_picture_url(None) is None


class TestFirstTopTrackLink:
    def test_returns_link_of_first_top_track(self):
        tracks = [{"link": "https://www.deezer.com/track/1483825282"}]
        assert deezer._first_top_track_link(tracks) == "https://www.deezer.com/track/1483825282"

    def test_uses_first_track_only(self):
        tracks = [
            {"link": "https://www.deezer.com/track/1"},
            {"link": "https://www.deezer.com/track/2"},
        ]
        assert deezer._first_top_track_link(tracks) == "https://www.deezer.com/track/1"

    def test_none_when_no_tracks(self):
        assert deezer._first_top_track_link([]) is None

    def test_none_when_link_missing(self):
        assert deezer._first_top_track_link([{"title": "no link"}]) is None

    def test_none_for_none_input(self):
        assert deezer._first_top_track_link(None) is None


class TestNewestAlbumId:
    def test_returns_album_with_latest_release_date(self):
        albums = [
            {"id": 1, "release_date": "2020-01-01"},
            {"id": 2, "release_date": "2023-05-01"},
            {"id": 3, "release_date": "2015-12-31"},
        ]
        assert deezer._newest_album_id(albums) == 2

    def test_skips_albums_without_release_date(self):
        albums = [
            {"id": 1, "release_date": ""},
            {"id": 2, "release_date": "2018-03-03"},
        ]
        assert deezer._newest_album_id(albums) == 2

    def test_none_when_no_albums(self):
        assert deezer._newest_album_id([]) is None

    def test_none_when_no_album_has_release_date(self):
        assert deezer._newest_album_id([{"id": 1, "title": "No date"}]) is None


class TestGenreNames:
    def test_returns_all_genre_names(self):
        album = {
            "genres": [
                {"id": 106, "name": "Electro"},
                {"id": 111, "name": "Techno/House"},
            ]
        }
        assert deezer._genre_names(album) == ["Electro", "Techno/House"]

    def test_empty_list_when_no_genres(self):
        assert deezer._genre_names({"title": "No genres"}) == []

    def test_skips_genres_without_name(self):
        album = {"genres": [{"id": 106}, {"id": 111, "name": "Dance"}]}
        assert deezer._genre_names(album) == ["Dance"]

    def test_deduplicates_repeated_names(self):
        album = {
            "genres": [
                {"id": 106, "name": "Rock"},
                {"id": 107, "name": "Rock"},
                {"id": 108, "name": "Pop"},
            ]
        }
        assert deezer._genre_names(album) == ["Rock", "Pop"]

    def test_empty_list_for_none_input(self):
        assert deezer._genre_names(None) == []


class TestToStickerBytes:
    def test_converts_to_512x512_webp(self):
        source = Image.new("RGB", (1000, 500), (255, 0, 0))
        buf = io.BytesIO()
        source.save(buf, format="PNG")

        result = deezer._to_sticker_bytes(buf.getvalue())

        sticker = Image.open(io.BytesIO(result))
        assert sticker.size == (512, 512)
        assert sticker.format == "WEBP"

    def test_upscales_small_images_to_512(self):
        source = Image.new("RGB", (100, 100), (0, 255, 0))
        buf = io.BytesIO()
        source.save(buf, format="PNG")

        result = deezer._to_sticker_bytes(buf.getvalue())

        sticker = Image.open(io.BytesIO(result))
        assert sticker.size == (512, 512)
