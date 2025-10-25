import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from models.event import JahrhunderthalleEvent

BASE_URL = "https://www.myticket-jahrhunderthalle.de"


def _get_admission_time(event_dto):
    detail_url = f'{BASE_URL}{event_dto["detailLink"]}'
    response = requests.get(detail_url)
    response.raise_for_status()

    hour, minute = None, None
    soup = BeautifulSoup(response.text, from_encoding="utf-8")
    event_detail = soup.find(class_="event-detail-meta")
    if event_detail is not None:
        information = event_detail.find_all("p")

        match = re.search(
            r"Einlass:\s+(\d{1,2}):(\d{2})\s*Uhr", information[1].text, re.IGNORECASE
        )
        if match:
            hour, minute = match.group(1), match.group(2)
    return hour, minute


def _create_event(event_dto):
    if event_dto["location"] in ("Parkplatz", "Kasino"):
        return

    hour, minute = _get_admission_time(event_dto)
    return JahrhunderthalleEvent(
        band=event_dto["title"],
        city="Frankfurt",
        location=f"Jahrhunderthalle - {event_dto['location']}",
        hint=(
            "Verlegt\n"
            if event_dto["postponed"]
            else (
                "" + "Abgesagt\n"
                if event_dto["canceled"]
                else "" + "Ausverkauft\n" if event_dto["sold"] else ""
            )
        ).strip(),
        date=datetime.strptime(event_dto["date"], "%d.%m.%y").date(),
        admission=(
            datetime.strptime(f"{hour}:{minute}", "%H:%M").time()
            if hour is not None
            else None
        ),
        beginn=datetime.strptime(event_dto["time"], "%H:%M").time(),
        id=event_dto["uid"],
        subtitle=event_dto["subline"],
    )


def load_events():
    response = requests.get(f"{BASE_URL}/events.json")
    response.raise_for_status()

    data = response.json()
    events: list[JahrhunderthalleEvent] = []
    for event_dto in tqdm(data["events"]):
        event = _create_event(event_dto)
        if event is not None:
            events.append(event)
    return events
