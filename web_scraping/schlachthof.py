from datetime import datetime
import re
from bs4 import BeautifulSoup
import requests
from tqdm import tqdm

from models.event import SchlachthofEvent


def _get_dates(soup: BeautifulSoup):
    date_str = soup.find_all("script")[1].next_sibling.next_sibling.text.strip()
    match = re.search(r"(\d{1,2}\.\d{1,2}\.\d{2,4})", date_str)
    if match:
        date = match.group(1)
    else:
        return None, None

    time_information_str = list(soup.find_all("div", class_="pr-[20px]")[0].children)[1].text.strip()
    admission_match = re.search(r"Einlass\s+(\d{1,2}:\d{2})", time_information_str, re.IGNORECASE)
    if admission_match:
        admission_time = admission_match.group(1)
    else:
        admission_time = None

    begin_match = re.search(r"Beginn\s+(\d{1,2}:\d{2})", time_information_str, re.IGNORECASE)
    if begin_match:
        begin_time = begin_match.group(1)
    else:
        begin_time = None

    admission = datetime.strptime(f"{date} {admission_time}", "%d.%m.%y %H:%M") if admission_time is not None else None
    beginn = datetime.strptime(f"{date} {begin_time}", "%d.%m.%y %H:%M") if begin_time is not None else None
    return admission, beginn


def _create_schlachthof_event(detail_url: str):
    response = requests.get(detail_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text)

    header = soup.find("div", class_="-ml-[2px] lg:-ml-[3px] 2xl:-ml-[4px]")
    band = header.text.strip()
    subheaders = (child.text.strip() for child in header.next_sibling.next_sibling.children)
    subtitle = "\t".join(subheader for subheader in subheaders if subheader)

    admission, beginn = _get_dates(soup)

    return SchlachthofEvent(
        band=band,
        city="Wiesbaden",
        location="Schlachthof",
        hint="", #TODO
        admission=admission,
        beginn=beginn,
        subtitle=subtitle
    )


def load_events():
    response = requests.get("https://schlachthof-wiesbaden.de/")
    response.raise_for_status()
    soup = BeautifulSoup(response.text)

    events: list[SchlachthofEvent] = []
    for separator in tqdm(soup.find_all('a', class_="scroll-mt-[220px]")):
        event_dto = separator.next_sibling.next_sibling
        detail_url = event_dto.get("href")
        event = _create_schlachthof_event(detail_url)
        events.append(event)
    return events
