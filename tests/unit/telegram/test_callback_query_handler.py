"""Unit tests for ``telegram.callback_query_handler``."""

import uuid

from models.event import Event, Source
from models.user import GenreUnsubscription, Interest, User
from telegram import callback_query_handler


class TestParseCallbackData:
    def test_parses_action_and_value(self):
        assert callback_query_handler._parse_callback_data("interested;123") == (
            "interested",
            "123",
        )

    def test_returns_none_when_no_separator(self):
        assert callback_query_handler._parse_callback_data("no-semicolon") is None

    def test_returns_none_when_too_many_parts(self):
        assert callback_query_handler._parse_callback_data("a;b;c") is None


class TestParseEventId:
    def test_parses_valid_uuid(self):
        value = str(uuid.uuid4())
        assert callback_query_handler._parse_event_id(value) == uuid.UUID(value)

    def test_returns_none_for_invalid_uuid(self):
        assert callback_query_handler._parse_event_id("not-a-uuid") is None

    def test_returns_none_for_non_string(self):
        assert callback_query_handler._parse_event_id(None) is None


class TestToggleGenreUnsubscription:
    def test_adds_unsubscription_when_not_present(self):
        user = User(id=1, chat_id=100)
        callback_query_handler._toggle_genre_unsubscription(user, genre_id=5)

        assert [u.genre_id for u in user.genre_unsubscriptions] == [5]

    def test_removes_unsubscription_when_present(self):
        user = User(id=1, chat_id=100)
        user.genre_unsubscriptions.append(GenreUnsubscription(genre_id=5))

        callback_query_handler._toggle_genre_unsubscription(user, genre_id=5)

        assert user.genre_unsubscriptions == []


class TestApplyInterest:
    def test_adds_interest(self):
        event = Event(
            id=uuid.uuid4(),
            dto_id="1",
            source=Source.BATSCHKAPP,
            city="F",
            location="L",
        )
        user = User(id=1, chat_id=100)

        callback_query_handler._apply_interest(user, event, is_interested=True)

        assert len(user.interest) == 1
        assert user.interest[0].event is event

    def test_removes_matching_interest(self):
        event = Event(
            id=uuid.uuid4(),
            dto_id="1",
            source=Source.BATSCHKAPP,
            city="F",
            location="L",
        )
        user = User(id=1, chat_id=100)
        user.interest.append(Interest(user_id=1, event_id=event.id))

        callback_query_handler._apply_interest(user, event, is_interested=False)

        assert user.interest == []

    def test_removing_keeps_other_interests(self):
        event = Event(
            id=uuid.uuid4(),
            dto_id="1",
            source=Source.BATSCHKAPP,
            city="F",
            location="L",
        )
        other_event_id = uuid.uuid4()
        user = User(id=1, chat_id=100)
        user.interest.append(Interest(user_id=1, event_id=event.id))
        user.interest.append(Interest(user_id=1, event_id=other_event_id))

        callback_query_handler._apply_interest(user, event, is_interested=False)

        assert [i.event_id for i in user.interest] == [other_event_id]
