"""Unit tests for the YouTube lookup helpers in ``web_scraping.audio_sample``."""

from web_scraping import audio_sample


class TestFirstResultLink:
    def test_returns_link_of_first_result(self):
        result = {"result": [{"link": "https://www.youtube.com/watch?v=abc123"}]}
        assert (
            audio_sample._first_result_link(result)
            == "https://www.youtube.com/watch?v=abc123"
        )

    def test_uses_first_result_only(self):
        result = {
            "result": [
                {"link": "https://www.youtube.com/watch?v=first"},
                {"link": "https://www.youtube.com/watch?v=second"},
            ]
        }
        assert audio_sample._first_result_link(result) == "https://www.youtube.com/watch?v=first"

    def test_none_when_no_results(self):
        assert audio_sample._first_result_link({"result": []}) is None

    def test_none_when_result_key_missing(self):
        assert audio_sample._first_result_link({}) is None

    def test_none_for_none_input(self):
        assert audio_sample._first_result_link(None) is None

    def test_none_when_link_missing(self):
        assert audio_sample._first_result_link({"result": [{"title": "no link"}]}) is None
