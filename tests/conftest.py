"""Shared fixtures for the top-level test suite.

Environment setup that must happen before any project module is imported now
lives in the root ``conftest.py`` so it also applies to the scraper tests in
the ``web_scraping/scrapers`` submodule.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from models import Base


@pytest.fixture
def session():
    """A fresh, isolated in-memory SQLAlchemy session with the full schema.

    Use this for tests that need to persist ORM objects (unit tests of logic
    that operates on ORM models, and later integration tests).
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db_session = Session(engine)
    try:
        yield db_session
    finally:
        db_session.close()
        engine.dispose()
