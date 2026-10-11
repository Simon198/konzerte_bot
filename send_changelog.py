import logging
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from models.changelog import Changelog
from repository import session
from telegram.prodcast_message import prodcast_message_to_all
from utils import TIMEZONE

HOME_FOLDER = os.path.abspath(os.path.dirname(__file__))
CHANGELOG_FOLDER = os.path.join(HOME_FOLDER, "changelog")

logger = logging.getLogger(__name__)


def read_changelog(changelog: Changelog):
    path = os.path.join(CHANGELOG_FOLDER, changelog.file_name)
    with open(path, "r") as file:
        md_content = file.read()

    return re.sub(r"#\s+(.*)\n", r"<b>\1</b>\n", md_content)


def prodcast_newest_changelog():  # pragma: no cover - DB + Telegram I/O
    try:
        logger.info("Start sending changelogs")
        changelog_file_names = sorted(os.listdir(CHANGELOG_FOLDER))

        file_name_query = select(Changelog.file_name)
        db_file_names = session.scalars(file_name_query).all()

        new_changelog = None
        for changelog_file_name in changelog_file_names:
            if changelog_file_name not in db_file_names:
                new_changelog = Changelog(
                    file_name=changelog_file_name,
                    sent_date=datetime.now(tz=ZoneInfo(TIMEZONE)),
                )
                session.add(new_changelog)

        if new_changelog is not None:
            message = read_changelog(new_changelog)
            prodcast_message_to_all(message, parse_mode="HTML")
        else:
            logger.info("No new changelog could be found")

        session.commit()
        logger.info("Sending changelogs completed")
    except:
        logger.exception("An error occured during sending changelogs")
