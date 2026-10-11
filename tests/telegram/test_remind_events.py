"""Unit tests for ``telegram.remind_events`` (concert reminders)."""

from datetime import date, timedelta

from models.event import Event, Source
from models.user import Interest, User
from telegram import remind_events


class TestLoadReminderDates:
    def test_returns_only_events_on_the_given_date(self, session, monkeypatch):
        monkeypatch.setattr(remind_events, "session", session)
        on_date = Event(
            dto_id="1", source=Source.BATSCHKAPP, band="A", city="F",
            location="L", event_date=date(2026, 5, 10),
        )
        other_date = Event(
            dto_id="2", source=Source.BATSCHKAPP, band="B", city="F",
            location="L", event_date=date(2026, 5, 11),
        )
        user = User(id=1, chat_id=100)
        user.interest.append(Interest(event=on_date))
        user.interest.append(Interest(event=other_date))
        session.add(user)
        session.commit()

        result = list(
            remind_events._load_reminder_dates(user, event_date=date(2026, 5, 10))
        )

        assert result == [on_date]


class TestRemindEventsToday:
    def test_sends_reminder_for_today(self, session, monkeypatch, fake_bot):
        monkeypatch.setattr(remind_events, "session", session)
        monkeypatch.setattr(remind_events, "telegram_bot", fake_bot)

        event = Event(
            dto_id="1", source=Source.BATSCHKAPP, band="A", city="F",
            location="L", event_date=date.today(),
        )
        user = User(id=1, chat_id=100)
        user.interest.append(Interest(event=event))
        session.add(user)
        session.commit()

        remind_events._remind_events_today(user)

        fake_bot.send_message.assert_called_once()
        text = fake_bot.send_message.call_args.kwargs["text"]
        assert "ERINNERUNG: Heute tritt auf" in text

    def test_ignores_events_on_other_dates(self, session, monkeypatch, fake_bot):
        monkeypatch.setattr(remind_events, "session", session)
        monkeypatch.setattr(remind_events, "telegram_bot", fake_bot)

        event = Event(
            dto_id="1", source=Source.BATSCHKAPP, band="A", city="F",
            location="L", event_date=date.today() + timedelta(days=30),
        )
        user = User(id=1, chat_id=100)
        user.interest.append(Interest(event=event))
        session.add(user)
        session.commit()

        remind_events._remind_events_today(user)

        fake_bot.send_message.assert_not_called()


class TestRemindEventsInAWeek:
    def test_sends_reminder_for_next_week(self, session, monkeypatch, fake_bot):
        monkeypatch.setattr(remind_events, "session", session)
        monkeypatch.setattr(remind_events, "telegram_bot", fake_bot)

        event = Event(
            dto_id="1", source=Source.BATSCHKAPP, band="A", city="F",
            location="L", event_date=date.today() + timedelta(weeks=1),
        )
        user = User(id=1, chat_id=100)
        user.interest.append(Interest(event=event))
        session.add(user)
        session.commit()

        remind_events._remind_events_in_a_week(user)

        fake_bot.send_message.assert_called_once()
        text = fake_bot.send_message.call_args.kwargs["text"]
        assert "In einer Woche tritt auf" in text
