from sqlalchemy import select

from models.event import Event
from repository import session

from . import telegram_bot


def send_events(chat_id: int):
    stmt = select(Event).order_by(Event.event_date, Event.beginn)
    events = [event for (event,) in session.execute(stmt).all()]
    column_value_fun_mapping = {
        "band": lambda event: event.band,
        "city": lambda event: event.city,
        "location": lambda event: event.location,
        "hint": lambda event: event.hint,
        "event_date": lambda event: event.event_date,
        "admission": lambda event: event.admission,
        "beginn": lambda event: event.beginn,
        "subtitle": lambda event: event.subtitle,
        "status": lambda event: event.status,
    }

    columns = "|" + "|".join(column_value_fun_mapping.keys()) + "|"
    separator = (
        "|" + "|".join("----------" for _ in range(len(column_value_fun_mapping))) + "|"
    )
    rows: list[str] = []
    for event in events:
        row = (
            "|"
            + "|".join(
                str(fun(event) or "") for fun in column_value_fun_mapping.values()
            )
            + "|"
        )
        rows.append(row)
    table_content = "\n".join(rows)

    html_text = f"""<pre>
{columns}
{separator}
{table_content}
</pre>"""
    telegram_bot.send_message(chat_id=chat_id, text=html_text, parse_mode="HTML")
