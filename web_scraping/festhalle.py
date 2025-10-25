import logging
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from .dto import EventDTO

logger = logging.getLogger(__name__)


def _parse_date(date_str: str):
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {date_str}")


def _parse_time(time_str: str, *prefix: str):
    hour, minute = None, None
    for pre in prefix:
        match = re.search(pre + r"[A-Za-z\n\s:]+(\d{1,2})([.:](\d{2}))?", time_str)
        if match is not None:
            hour = match.group(1)
            minute = match.group(3) or "00"

    if hour is None:
        return None
    return datetime.strptime(f"{hour}:{minute}", "%H:%M").time()


def _get_dates(soup):
    content = soup.find(id="content")

    date_str = content.find("h2").text  # e.g. Sa, 04.10.2025
    match = re.search(r"\b\d{1,2}\.\d{1,2}\.(?:\d{2}|\d{4})\b", date_str)
    if not match:
        return None, None, None, None

    date = _parse_date(match.group())

    lis = content.find(
        class_="m-text-image m-text-image--image-left l-deactivate-gap"
    ).find_all("li")
    time_str = "\n".join(li.text for li in lis)

    beginn = _parse_time(
        time_str, "Beginn", "Veranstaltungszeit"
    )  # e.g. Veranstaltungszeiten: 19:10 Uhr - 19:30 Uhr Vorgruppe ...
    admission = _parse_time(time_str, "Einlass")  # e.g. Einlass ab 17:45 Uhr
    hint = "\n".join([li.text.strip() for li in lis[2:]])

    return date, beginn, admission, hint


def _create_festhalle_event(hit):
    url: str = hit["interneturl"]
    if not url.startswith("http"):
        url = "https://" + url
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, from_encoding="utf-8")

    date, beginn, admission, hint = _get_dates(soup)

    return EventDTO(
        id=hit["eventid"],
        band="Montez",
        city=hit["cityname"],
        location=hit["venuename"],
        hint=hint,
        date=date,
        admission=admission,
        beginn=beginn,
    )


def load_events():
    logger.info("Start loading Festhalle events")
    start_time = time.time()
    page = 1
    page_size = 50
    total = 51
    progress = None
    events: list[EventDTO] = []

    while (page - 1) * page_size < total:
        response = requests.get(
            f"https://api.messefrankfurt.com/service/esb_api/event-service/api/2.1/public/event/search/de-DE?q=&orderBy=date&pageNumber={page}&pageSize={page_size}&year=&orSearchFallback=false&format=Konzerte+und+Events&city=Frankfurt+am+Main",
            headers={"Apikey": "dD9LNnLjFXr3wABPY1vOwoFHe8OgWY4Gabm6qA4pejRR7IrXHSs="},
        )
        response.raise_for_status()

        data = response.json()
        result = data["result"]

        total = result["metaData"]["hitsTotal"]
        if progress is None:
            progress = tqdm(total=total, desc="Processing")

        hits = result["hits"]
        for hit in hits:
            if hit["formatname"] != "Konzert":
                continue

            event = _create_festhalle_event(hit)
            events.append(event)

        page += 1
        progress.update(len(hits))

    progress.close()
    logger.info(
        f"Retrieved {len(events)} Festhalle events in {(time.time() - start_time) / 60:.2f}"
    )
    return events


if __name__ == "__main__":
    load_events()
