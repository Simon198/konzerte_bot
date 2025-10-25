from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Base

engine = create_engine("sqlite:///concerts.db", echo=True)
Base.metadata.create_all(engine)

session = Session(engine)
