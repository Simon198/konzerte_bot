import configparser
import logging
import os
from logging.handlers import TimedRotatingFileHandler

from telegram import ADMIN_CHAT_ID, admin_bot

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
telegram_formatter = logging.Formatter("[%(levelname)s] %(message)s")

logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

LEVEL_EMOJI = {
    logging.DEBUG: "🐛",  # Debug
    logging.INFO: "ℹ️",  # Info
    logging.WARNING: "⚠️",  # Warning
    logging.ERROR: "❌",  # Error
    logging.CRITICAL: "🔥",  # Critical
}


class TelegramLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, log_record: logging.LogRecord):
        try:
            admin_bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"{LEVEL_EMOJI[log_record.levelno]} {self.format(log_record)}",
                disable_notification=log_record.levelno < logging.WARNING,
            )
        except:
            self.handleError(log_record)


root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

telegram_handler = TelegramLogHandler()
telegram_handler.setLevel(logging.INFO)
root_logger.addHandler(telegram_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)


cfg = configparser.ConfigParser()
cfg.read("/etc/konzerte_bot/config.ini")
log_folder = cfg.get("logging", "log_folder", fallback="./logs")
try:
    os.makedirs(log_folder, exist_ok=True)
except PermissionError:
    root_logger.exception(f"⚠️ Cannot create {log_folder}, falling back to './logs'")
    log_folder = "./logs"
    os.makedirs(log_folder, exist_ok=True)

log_file = os.path.join(log_folder, "application.log")

file_handler = TimedRotatingFileHandler(
    log_file,
    when="midnight",  # rotate every midnight
    interval=1,  # every 1 day
    backupCount=30,  # keep 30 days of logs
    encoding="utf-8",
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)
