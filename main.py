from dotenv import load_dotenv

load_dotenv()

import logger
import telegram.bot
import telegram.remind_events
import telegram.send_events
import web_scraping

try:
    telegram.bot.poll_updates()
    web_scraping.load_and_persist_events()
    telegram.send_events.send_events()
    telegram.remind_events.remind_events()
except:
    logger.root_logger.exception("An uncatched error has occurred")
