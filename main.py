from dotenv import load_dotenv

load_dotenv()

import logger
import telegram.bot
import telegram.send_events
import web_scraping

try:
    web_scraping.load_and_persist_events()
    telegram.bot.poll_updates()
    telegram.send_events.send_events()
except:
    logger.root_logger.exception("An uncatched error has occurred")
