"""Database connection and per-request sessions.

Each service owns its own database. Its location comes from the DATABASE_URL
environment variable; without it, a SQLite file named data.db in the current
folder is used.
"""

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")

# SQLite normally lets a connection be used only by the thread that opened it.
# FastAPI serves requests on several threads, so that check is switched off.
# Other databases neither need nor accept this option.
if DATABASE_URL.startswith("sqlite"):
    connection_options = {"check_same_thread": False}
else:
    connection_options = {}

engine = create_engine(DATABASE_URL, connect_args=connection_options)

# Creates a new database session each time it is called.
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Parent class for every database model (table) in this service."""


def get_db() -> Iterator[Session]:
    """Give one request its own database session, and always close it afterwards.

    Framework note: FastAPI calls this for every endpoint that declares
    `Depends(get_db)`. Code before `yield` runs before the endpoint, the
    session is handed to the endpoint at `yield`, and the `finally` block runs
    once the endpoint has finished, even if it raised an error.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
