import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from models.event import BatschkappEvent


def _create_batschkapp_event(event_dto):
    admission_datetime = datetime.strptime(event_dto["einlass"], "%Y-%m-%d %H:%M:%S")
    begin_datetime = datetime.strptime(event_dto["beginn"], "%Y-%m-%d %H:%M:%S")
    return BatschkappEvent(
        id=event_dto["id"],
        band=event_dto["TourId"]["titel"],
        city="Frankfurt",
        location=event_dto["VeranstaltungsortId"]["veranstaltungsort"],
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

    return [
        _create_batschkapp_event(event_dto)
        for event_dto in tqdm(events_dto)
        if event_dto["TourId"]["RubrikId"]["name"] == "Konzert"
    ]
