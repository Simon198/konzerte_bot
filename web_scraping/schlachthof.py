import logging
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from .dto import EventDTO

logger = logging.getLogger(__name__)


def _get_dates(soup: BeautifulSoup):
    date_str = soup.find_all("script")[1].next_sibling.next_sibling.text.strip()
    match = re.search(r"(\d{1,2}\.\d{1,2}\.\d{2,4})", date_str)
    if not match:
        return None, None, None

    date = datetime.strptime(match.group(1), "%d.%m.%y").date()

    time_information_str = list(soup.find_all("div", class_="pr-[20px]")[0].children)[
        1
    ].text.strip()
    admission_match = re.search(
        r"Einlass\s+(\d{1,2}:\d{2})", time_information_str, re.IGNORECASE
    )
    if admission_match:
        admission_time = admission_match.group(1)
    else:
        admission_time = None

    begin_match = re.search(
        r"Beginn\s+(\d{1,2}:\d{2})", time_information_str, re.IGNORECASE
    )
    if begin_match:
        begin_time = begin_match.group(1)
    else:
        begin_time = None

    admission = (
        datetime.strptime(admission_time, "%H:%M").time()
        if admission_time is not None
        else None
    )
    beginn = (
        datetime.strptime(begin_time, "%H:%M").time()
        if begin_time is not None
        else None
    )
    return date, admission, beginn


def _create_schlachthof_event(detail_url: str):
    id = re.match(r"https://schlachthof-wiesbaden.de/events/(.*)", detail_url).group(1)
    response = requests.get(detail_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text)

    header = soup.find("div", class_="-ml-[2px] lg:-ml-[3px] 2xl:-ml-[4px]")
    band = header.text.strip()
    subheaders = (
        child.text.strip() for child in header.next_sibling.next_sibling.children
    )
    subtitle = "\t".join(subheader for subheader in subheaders if subheader)

    date, admission, beginn = _get_dates(soup)

    return EventDTO(
        id=id,
        source="Schlachthof",
        band=band,
        city="Wiesbaden",
        location="Schlachthof",
        hint="",  # TODO
        date=date,
        admission=admission,
        beginn=beginn,
        subtitle=subtitle,
    )


def load_events():
    logger.info("Start loading Schlachthof events")
    start_time = time.time()
    response = requests.get("https://schlachthof-wiesbaden.de/")
    response.raise_for_status()
    soup = BeautifulSoup(response.text)

    events: list[EventDTO] = []
    for separator in tqdm(soup.find_all("a", class_="scroll-mt-[220px]")):
        event_dto = separator.next_sibling.next_sibling
        detail_url = event_dto.get("href")
        event = _create_schlachthof_event(detail_url)
        events.append(event)

    logger.info(
        f"Retrieved {len(events)} Schlachthof events in {(time.time() - start_time) / 60:.2f}"
    )
    return events
