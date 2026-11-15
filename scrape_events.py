from dotenv import load_dotenv

load_dotenv()

# Configures the root logging handlers (Telegram admin + rotating file).
import logger
import web_scraping


if __name__ == "__main__":
    web_scraping.load_and_persist_events()
