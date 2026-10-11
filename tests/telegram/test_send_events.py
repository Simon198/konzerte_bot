"""Unit tests for ``telegram.send_events`` (the recommendation query)."""

from datetime import date
from types import SimpleNamespace

from models.event import Event, Source
from models.user import Observed, SourceUnsubscription, User
from telegram import send_events


class TestSendEventsToUser:
    def test_sends_only_unobserved_and_subscribed(self, session, monkeypatch, fake_bot):
        monkeypatch.setattr(send_events, "session", session)
        sent = []

        def fake_send(chat_id, text, reply_markup=None):
            sent.append((chat_id, text))
            return SimpleNamespace(id=len(sent))

        fake_bot.send_message.side_effect = fake_send
        monkeypatch.setattr(send_events, "telegram_bot", fake_bot)

        observed = Event(
            dto_id="1", source=Source.BATSCHKAPP, band="Observed", city="F",
            location="L", event_date=date(2026, 6, 1),
        )
        unsubscribed = Event(
            dto_id="2", source=Source.FESTHALLE, band="Unsubscribed", city="F",
            location="L", event_date=date(2026, 6, 2),
        )
        candidate = Event(
            dto_id="3", source=Source.BATSCHKAPP, band="Band C", city="F",
            location="L", event_date=date(2026, 6, 3),
        )
        session.add_all([observed, unsubscribed, candidate])
        session.flush()

        user = User(id=1, chat_id=100)
        user.observed.append(Observed(event=observed, message_id=999))
        user.source_unsubscriptions.append(
            SourceUnsubscription(source=Source.FESTHALLE)
        )
        session.add(user)
        session.commit()

        send_events.send_events_to_user(user, limit=10)

        assert [text for _, text in sent] == ["03.06.2026 - Band C (F-L)"]
        assert sent[0][0] == 100

        # The sent event is now recorded as observed for the user.
        assert candidate.id in {o.event_id for o in user.observed}

    def test_respects_limit(self, session, monkeypatch, fake_bot):
        monkeypatch.setattr(send_events, "session", session)
        fake_bot.send_message.side_effect = lambda **kwargs: SimpleNamespace(id=1)
        monkeypatch.setattr(send_events, "telegram_bot", fake_bot)

        session.add_all([
            Event(
                dto_id="1", source=Source.BATSCHKAPP, band="A", city="F",
                location="L", event_date=date(2026, 6, 1),
            ),
            Event(
                dto_id="2", source=Source.BATSCHKAPP, band="B", city="F",
                location="L", event_date=date(2026, 6, 2),
            ),
        ])
        session.add(User(id=1, chat_id=100))
        session.commit()

        send_events.send_events_to_user(session.get(User, 1), limit=1)

        assert fake_bot.send_message.call_count == 1

    def test_no_events_sends_nothing(self, session, monkeypatch, fake_bot):
        monkeypatch.setattr(send_events, "session", session)
        monkeypatch.setattr(send_events, "telegram_bot", fake_bot)
        session.add(User(id=1, chat_id=100))
        session.commit()

        send_events.send_events_to_user(session.get(User, 1), limit=10)

        fake_bot.send_message.assert_not_called()
