from sqlalchemy import and_, not_, select
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from models.event import Event
from models.user import User, observed_events_table
from repository import session

from . import telegram_bot


def send_events_to_user(user: User):
    stmt = (
        select(Event)
        .where(
            and_(
                not_(
                    Event.id.in_(
                        select(observed_events_table.c.event_id)
                        .distinct()
                        .where(observed_events_table.c.user_id == user.id)
                    )
                ),
                not_(
                    Event.source.in_(
                        unsubscription.source
                        for unsubscription in user.source_unsubscriptions
                    )
                ),
            )
        )
        .order_by(Event.event_date, Event.beginn)
        .limit(5)
    )

    events: list[Event] = [event for (event,) in session.execute(stmt).all()]
    user.observed_events.extend(events)

    for event in events:
        text = f"{event.event_date} - {event.band} ({event.city}-{event.location})"
        if event.subtitle:
            text += "\n" + event.subtitle
        if event.admission or event.beginn:
            parts = []
            if event.admission:
                parts.append(f"Einlass: {event.admission}")
            if event.beginn:
                parts.append(f"Beginn: {event.beginn}")
            text += "\n" + "; ".join(parts)
        if event.hint:
            text += "\n" + event.hint
        if event.status:
            text += "\nStatus: " + event.status

        markup = InlineKeyboardMarkup()
        btn_yes = InlineKeyboardButton(
            "✅ Interesse", callback_data=f"interested;{event.id}"
        )
        btn_no = InlineKeyboardButton(
            "❌ Kein Interesse", callback_data="not_interested"
        )
        markup.add(btn_yes, btn_no)

        telegram_bot.send_message(chat_id=user.chat_id, text=text, reply_markup=markup)
    session.commit()


def send_events():
    for (user,) in session.execute(select(User)):
        send_events_to_user(user)


if __name__ == "__main__":
    send_events()
