"""Unit tests for the DSGVO data export helpers in ``telegram.mydata``."""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

from models.event import Event, Source
from models.feature import Feature
from models.user import Interest, Observed, SourceUnsubscription, User
from telegram import mydata
from telegram.mydata import _build_summary, _event_fields, build_user_data


def _build_user(session):
    event = Event(
        dto_id="1",
        source=Source.BATSCHKAPP,
        band="Band A",
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
    user.features.append(Feature(text="Mehr Metal"))
    session.add(user)
    session.commit()
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
        event = Event(band="X", city="Y", location="Z", event_date=date(2026, 5, 10))
        assert _event_fields(event) == {
            "band": "X",
            "city": "Y",
            "location": "Z",
            "event_date": "2026-05-10",
        }

    def test_event_without_date(self):
        event = Event(band="X", city="Y", location="Z", event_date=None)
        assert _event_fields(event)["event_date"] is None


class TestBuildUserData:
    def test_user_fields(self, session):
        user, _ = _build_user(session)
        data = build_user_data(user)["user"]
        assert data["id"] == 1
        assert data["chat_id"] == 100
        assert data["username"] == "alice"
        assert data["is_admin"] is True
        assert data["consent_given"] is True
        assert data["consent_version"] == "2026-10-10"

    def test_interests(self, session):
        user, event = _build_user(session)
        interests = build_user_data(user)["interests"]
        assert len(interests) == 1
        assert interests[0]["event_id"] == str(event.id)
        assert interests[0]["band"] == "Band A"
        assert interests[0]["event_date"] == "2026-05-10"

    def test_observed_events(self, session):
        user, event = _build_user(session)
        observed = build_user_data(user)["observed_events"]
        assert len(observed) == 1
        assert observed[0]["event_id"] == str(event.id)
        assert observed[0]["band"] == "Band A"
        assert observed[0]["message_id"] == 555

    def test_source_unsubscriptions(self, session):
        user, _ = _build_user(session)
        assert build_user_data(user)["source_unsubscriptions"] == ["Festhalle"]

    def test_features(self, session):
        user, _ = _build_user(session)
        features = build_user_data(user)["features"]
        assert len(features) == 1
        assert features[0]["text"] == "Mehr Metal"
        assert features[0]["id"] == str(user.features[0].id)


class TestBuildSummary:
    def test_contains_dsgvo_fields(self, session):
        user, _ = _build_user(session)
        summary = _build_summary(user)
        assert "Art. 15 DSGVO" in summary
        assert "Nutzer-ID: 1" in summary
        assert "@alice" in summary
        assert "Admin: ja" in summary
        assert "Band A" in summary
        assert "Festhalle" in summary
        assert "Mehr Metal" in summary

    def test_no_consent_and_no_username(self, session):
        user = User(
            id=2, chat_id=200, username=None, is_admin=False, consent_given=False
        )
        session.add(user)
        session.commit()
        summary = _build_summary(user)
        assert "Benutzername: (keiner)" in summary
        assert "Admin: nein" in summary
        assert "Einwilligung: nicht erteilt" in summary


class TestSendUserData:
    def test_sends_summary_and_json_document(self, session, monkeypatch):
        fake_bot = MagicMock()
        monkeypatch.setattr(mydata, "telegram_bot", fake_bot)

        user = User(id=1, chat_id=100, username="alice", consent_given=True)
        session.add(user)
        session.commit()

        mydata.send_user_data(user)

        fake_bot.send_message.assert_called_once()
        assert fake_bot.send_message.call_args.kwargs["chat_id"] == 100

        fake_bot.send_document.assert_called_once()
        document = fake_bot.send_document.call_args.kwargs["document"]
        assert document.file_name == "konzert_bot_daten.json"
