import logging
import threading
import time

import schedule

import telegram.remind_events
import web_scraping
from utils import TIMEZONE

logger = logging.getLogger(__name__)


def run_scheduler():
    schedule.every().day.at("09:00", TIMEZONE).do(telegram.remind_events.remind_events)
    schedule.every().day.at("17:00", TIMEZONE).do(web_scraping.load_and_persist_events)
    logger.info("Scheduler started successfully")

    while True:
        schedule.run_pending()
        time.sleep(1)


def run_scheduler_in_background():
    """
    Run scheduler in a background thread (non-blocking).
    """
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    return scheduler_thread


if __name__ == "__main__":
    web_scraping.load_and_persist_events()
