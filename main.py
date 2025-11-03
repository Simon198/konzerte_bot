import logging

from dotenv import load_dotenv

import telegram.bot
import web_scraping

load_dotenv()

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


events = web_scraping.load_and_persist_events()
telegram.bot.run_telegram_bot()
