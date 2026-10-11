import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Base

# The database URL can be overridden via the environment so that tests (and
# alternative deployments) can point at an isolated database instead of the
# production ``concerts.db`` file.
DATABASE_URL = os.getenv("KONZERTE_BOT_DATABASE_URL", "sqlite:///concerts.db")

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)

session = Session(engine)
