from dotenv import load_dotenv

load_dotenv()

# Configures the root logging handlers (Telegram admin + rotating file).
import logger
import telegram.remind_events


if __name__ == "__main__":
    telegram.remind_events.remind_events()
