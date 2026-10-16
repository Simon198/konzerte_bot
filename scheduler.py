import logging
import threading
import time

import schedule

import telegram.remind_events
import web_scraping
from utils import TIMEZONE

logger = logging.getLogger(__name__)


def run_scheduler():
    try:
        schedule.every().day.at("09:00", TIMEZONE).do(telegram.remind_events.remind_events)
        schedule.every().day.at("17:00", TIMEZONE).do(web_scraping.load_and_persist_events)
        logger.info("Scheduler started successfully")

        # Immediately begin scraping events in the background so the bot stays
        # reachable and events are available right after startup.
        web_scraping.load_and_persist_events_async()

        while True:
            schedule.run_pending()
            time.sleep(1)
    except:
        # Log via the configured handlers (Telegram admin + file) instead of
        # letting the daemon thread die silently with only a stderr traceback.
        logger.exception("Scheduler failed unexpectedly")


def run_scheduler_in_background():
    """
    Run scheduler in a background thread (non-blocking).
    """
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    return scheduler_thread


if __name__ == "__main__":
    web_scraping.load_and_persist_events()
