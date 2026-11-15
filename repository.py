import functools
import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import scoped_session, sessionmaker

# The database URL can be overridden via the environment so that tests (and
# alternative deployments) can point at an isolated database instead of the
# production ``concerts.db`` file.
DATABASE_URL = os.getenv("KONZERTE_BOT_DATABASE_URL", "sqlite:///concerts.db")

engine = create_engine(DATABASE_URL)

if engine.dialect.name == "sqlite":
    # SQLite serialises writes. WAL journaling plus a generous busy timeout let
    # brief concurrent writes wait for the lock instead of failing with
    # "database is locked", which happened once Telegram updates were handled by
    # several worker threads in parallel.
    @event.listens_for(engine, "connect")
    def _configure_sqlite(dbapi_connection, connection_record):  # pragma: no cover - DB connection config
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# The schema is managed exclusively by Alembic migrations (``alembic upgrade
# head`` is run during deployment). Do not call ``create_all`` here: it would
# create tables outside Alembic's version history and let the schema drift.
#
# A single shared Session is *not* thread-safe. telebot processes updates in a
# pool of worker threads, so we use a scoped session to give every thread its
# own Session. Sharing one Session across threads corrupted its state and forced
# a bot restart whenever a parallel update failed.
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
session = scoped_session(SessionLocal)


def with_db_session(func):
    """Wrap a Telegram handler so its session is always left clean.

    Rolls back on error and disposes of the thread-scoped session afterwards, so
    a failed update can never leave a poisoned session behind for the next
    update handled by the same worker thread.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # pragma: no cover - DB session management
        try:
            return func(*args, **kwargs)
        except Exception:
            session.rollback()
            raise
        finally:
            remove = getattr(session, "remove", None)
            if remove is not None:
                remove()

    return wrapper
