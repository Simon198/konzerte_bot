"""Unit tests for the DSGVO data export helpers in ``telegram.mydata``."""

import uuid
from datetime import date, datetime, timezone

from models.band import Band
from models.event import Event, Source
from models.genre import Genre
from models.user import Interest, Observed, SourceUnsubscription, GenreUnsubscription, User
from telegram.mydata import (
    _build_json_bytes,
    _build_summary,
    _event_fields,
    build_user_data,
)


def _build_user():
    event = Event(
        id=uuid.uuid4(),
        dto_id="1",
        source=Source.BATSCHKAPP,
        band=Band(name="Band A"),
        city="Frankfurt",
        location="Batschkapp",
        event_date=date(2026, 5, 10),
    )
    user = User(
        id=1,
        chat_id=100,
        username="alice",
        is_admin=True,
        consent_given=True,
        consent_date=datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc),
        consent_version="2026-10-10",
    )
    user.interest.append(Interest(event=event))
    user.observed.append(Observed(event=event, message_id=555))
    user.source_unsubscriptions.append(SourceUnsubscription(source=Source.FESTHALLE))
    user.genre_unsubscriptions.append(
        GenreUnsubscription(genre_id=7, genre=Genre(id=7, name="Metal"))
    )
    return user, event


class TestEventFields:
    def test_none(self):
        assert _event_fields(None) == {
            "band": None,
            "city": None,
            "location": None,
            "event_date": None,
        }

    def test_event(self):
        event = Event(band=Band(name="X"), city="Y", location="Z", event_date=date(2026, 5, 10))
        assert _event_fields(event) == {
            "band": "X",
            "city": "Y",
            "location": "Z",
            "event_date": "2026-05-10",
        }

    def test_event_without_date(self):
        event = Event(band=Band(name="X"), city="Y", location="Z", event_date=None)
        assert _event_fields(event)["event_date"] is None


class TestBuildUserData:
    def test_user_fields(self):
        user, _ = _build_user()
        data = build_user_data(user)["user"]
        assert data["id"] == 1
        assert data["chat_id"] == 100
        assert data["username"] == "alice"
        assert data["is_admin"] is True
        assert data["consent_given"] is True
        assert data["consent_version"] == "2026-10-10"

    def test_interests(self):
        user, event = _build_user()
        interests = build_user_data(user)["interests"]
        assert len(interests) == 1
        assert interests[0]["event_id"] == str(event.id)
        assert interests[0]["band"] == "Band A"

    def test_observed_events(self):
        user, event = _build_user()
        observed = build_user_data(user)["observed_events"]
        assert len(observed) == 1
        assert observed[0]["event_id"] == str(event.id)
        assert observed[0]["message_id"] == 555

    def test_source_unsubscriptions(self):
        user, _ = _build_user()
        assert build_user_data(user)["source_unsubscriptions"] == ["Festhalle"]

    def test_genre_unsubscriptions(self):
        user, _ = _build_user()
        assert build_user_data(user)["genre_unsubscriptions"] == ["Metal"]


class TestBuildSummary:
    def test_contains_dsgvo_fields(self):
        user, _ = _build_user()
        summary = _build_summary(user)
        assert "Art. 15 DSGVO" in summary
        assert "Nutzer-ID: 1" in summary
        assert "@alice" in summary
        assert "Admin: ja" in summary
        assert "Band A" in summary

    def test_no_consent_and_no_username(self):
        user = User(id=2, chat_id=200, username=None, is_admin=False, consent_given=False)
        summary = _build_summary(user)
        assert "Benutzername: (keiner)" in summary
        assert "Admin: nein" in summary
        assert "Einwilligung: nicht erteilt" in summary

    def test_lists_genre_unsubscriptions(self):
        user, _ = _build_user()
        summary = _build_summary(user)
        assert "Abgewählte Genres:" in summary
        assert "Metal" in summary

    def test_orphaned_interest_without_event(self):
        user = User(id=3, chat_id=300, username="bob", consent_given=True)
        orphan_id = uuid.uuid4()
        user.interest.append(Interest(event_id=orphan_id))
        summary = _build_summary(user)
        assert "Konzert nicht mehr verfügbar" in summary
        assert str(orphan_id) in summary


class TestBuildJsonBytes:
    def test_returns_json_bytes(self):
        user, _ = _build_user()
        data = _build_json_bytes(user)
        assert isinstance(data, bytes)
        assert b'"username": "alice"' in data
