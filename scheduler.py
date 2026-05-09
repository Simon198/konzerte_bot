import logging
import threading
import time
import schedule

import telegram.remind_events
import telegram.send_events
import web_scraping

logger = logging.getLogger(__name__)


def _load_and_send_events():
    web_scraping.load_and_persist_events()
    telegram.send_events.send_events()


def run_scheduler():
    schedule.every().day.at("09:00", "Europe/Berlin").do(
        telegram.remind_events.remind_events
    )
    schedule.every().day.at("17:00", "Europe/Berlin").do(_load_and_send_events)
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
