from dotenv import load_dotenv

load_dotenv()

import logger
import scheduler
import telegram
import send_changelog

try:
    telegram.message_handler.setup_bot_commands()
    send_changelog.prodcast_newest_changelog()
    scheduler.run_scheduler_in_background()
    telegram.telegram_bot.infinity_polling()
except:
    logger.root_logger.exception("An uncatched error has occurred")
