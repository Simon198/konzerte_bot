"""Unit tests for changelog helpers in ``send_changelog``."""

import send_changelog
from models.changelog import Changelog


class TestReadChangelog:
    def test_replaces_headings_with_bold_tags(self, tmp_path, monkeypatch):
        changelog_file = tmp_path / "CHANGELOG_0.1.md"
        changelog_file.write_text("# Version 0.1\n\n- Item 1\n", encoding="utf-8")
        monkeypatch.setattr(send_changelog, "CHANGELOG_FOLDER", str(tmp_path))

        result = send_changelog.read_changelog(
            Changelog(file_name="CHANGELOG_0.1.md")
        )

        assert "<b>Version 0.1</b>" in result
        assert "- Item 1" in result
        assert "# Version" not in result

    def test_multiple_headings(self, tmp_path, monkeypatch):
        changelog_file = tmp_path / "c.md"
        changelog_file.write_text("# A\n# B\n", encoding="utf-8")
        monkeypatch.setattr(send_changelog, "CHANGELOG_FOLDER", str(tmp_path))

        result = send_changelog.read_changelog(Changelog(file_name="c.md"))
        assert result == "<b>A</b>\n<b>B</b>\n"
