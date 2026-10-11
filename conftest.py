"""Root test configuration.

Sets environment variables before any project module is imported. The
application has import-time side effects (it creates Telegram bot instances and
a database engine/session), so these must be in place before test collection.

Living at the repository root, this conftest applies to *all* tests, including
the scraper tests in the ``web_scraping/scrapers`` submodule.
"""

import os

import pytest

os.environ["TOKEN"] = "000000000:TEST_TOKEN_PLACEHOLDER"
os.environ["ADMIN_TOKEN"] = "000000000:TEST_TOKEN_PLACEHOLDER"
os.environ["ADMIN_CHAT_ID"] = "0"
os.environ["KONZERTE_BOT_DATABASE_URL"] = "sqlite:///:memory:"


def pytest_collection_modifyitems(config, items):
    """Tag every test that is not marked ``integration`` as ``unit``."""
    for item in items:
        if item.get_closest_marker("integration") is None:
            item.add_marker(pytest.mark.unit)
