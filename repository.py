import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# The database URL can be overridden via the environment so that tests (and
# alternative deployments) can point at an isolated database instead of the
# production ``concerts.db`` file.
DATABASE_URL = os.getenv("KONZERTE_BOT_DATABASE_URL", "sqlite:///concerts.db")

# The schema is managed exclusively by Alembic migrations (``alembic upgrade
# head`` is run during deployment). Do not call ``create_all`` here: it would
# create tables outside Alembic's version history and let the schema drift.
engine = create_engine(DATABASE_URL)

session = Session(engine)
