import json
import logging
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from models.event import Source

from .dto import EventDTO

logger = logging.getLogger(__name__)


def _create_batschkapp_event(event_dto):
    admission_datetime = datetime.strptime(event_dto["einlass"], "%Y-%m-%d %H:%M:%S")
    begin_datetime = datetime.strptime(event_dto["beginn"], "%Y-%m-%d %H:%M:%S")
    location = event_dto["VeranstaltungsortId"]["veranstaltungsort"]
    city = "Offenbach" if location == "Stadthalle Offenbach" else "Frankfurt"
    return EventDTO(
        id=event_dto["id"],
        source=Source.BATSCHKAPP,
        band=event_dto["TourId"]["titel"],
        city=city,
        location=location,
        hint="; ".join(
            [
                textes["Hinweistextes_id"]["hinweistext"]
                for textes in event_dto["EventHinweistextes"]
            ]
        ),
        date=begin_datetime.date(),
        beginn=begin_datetime.time(),
        admission=admission_datetime.time(),
        subtitle=event_dto["TourId"]["untertitel"],
        status=event_dto["status"],
    )


def load_events():
    logger.info("Start loading Batschkapp events")
    start_time = time.time()
    response = requests.get("https://www.batschkapp.net/")
    response.raise_for_status()
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, from_encoding="utf-8")

    dto: str = (
        soup.find_all("script")[-1]
        .text.strip()
        .removeprefix("self.__next_f.push(")
        .removesuffix(")")
    )
    data = json.loads(dto)
    assert data[0] == 1
    events_dto = json.loads(data[1].strip().removeprefix("d:"))[-1]["children"][2][3][
        "children"
    ][2][3]["events"]

    events = [
        _create_batschkapp_event(event_dto)
        for event_dto in tqdm(events_dto)
        if event_dto["TourId"]["RubrikId"]["name"] == "Konzert"
    ]
    logger.info(
        f"Retrieved {len(events)} Batschkapp events in {(time.time() - start_time) / 60:.2f}"
    )
    return events
