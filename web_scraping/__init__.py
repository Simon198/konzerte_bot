import logging

from . import batschkapp, festhalle, jahrhunderthalle, schlachthof
from .dto import EventDTO

logger = logging.getLogger(__name__)


def load_all_events():
    events: list[EventDTO] = []

    try:
        events.extend(batschkapp.load_events())
    except:
        logging.exception("The events of Batschkapp could not be loaded")

    try:
        events.extend(festhalle.load_events())
    except:
        logging.exception("The events of Festhalle could not be loaded")

    try:
        events.extend(jahrhunderthalle.load_events())
    except:
        logging.exception("The events of Jahrhunderthalle could not be loaded")

    try:
        events.extend(schlachthof.load_events())
    except:
        logging.exception("The events of Schlachthof could not be loaded")

    return events
