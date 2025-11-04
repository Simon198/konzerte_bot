import logging

from dotenv import load_dotenv

import telegram.bot
import telegram.send_events
import web_scraping

load_dotenv()

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


web_scraping.load_and_persist_events()
telegram.bot.poll_updates()
telegram.send_events.send_events()
