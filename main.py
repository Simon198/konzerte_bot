from dotenv import load_dotenv

load_dotenv()

import logger
import scheduler
import telegram

try:
    telegram.message_handler.setup_bot_commands()
    scheduler.run_scheduler_in_background()
    telegram.telegram_bot.infinity_polling()
except:
    logger.root_logger.exception("An uncatched error has occurred")
