"""Unit tests for ``telegram.command`` (the bot command registry)."""

from telegram.command import Commands


def test_commands_have_expected_members():
    assert {command.name for command in Commands} == {
        "start",
        "sources",
        "genres",
        "go",
        "next",
        "changelog",
        "datenschutz",
        "mydata",
        "pairings",
        "delete",
    }


def test_every_command_has_a_description():
    for command in Commands:
        assert command.value.strip() != ""
