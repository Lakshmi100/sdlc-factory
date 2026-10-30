"""Shared test setup for the customers service.

pytest loads this file automatically. Any test with a parameter named `client`
receives the HTTP test client created by the fixture below.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


# Framework note: `@pytest.fixture` registers this function as a fixture.
# pytest runs it before each test that has a parameter named `client`. The
# test receives the value at `yield`, and the code after `yield` runs once the
# test has finished.
@pytest.fixture
def client() -> Iterator[TestClient]:
    """HTTP test client for the app, backed by a fresh in-memory database.

    Every test gets its own empty database, so tests never affect each other.
    Requests made with the client run the real app in this process; no server
    or port is needed.
    """
    # "sqlite://" with no file name is an in-memory database. StaticPool makes
    # every connection share it; otherwise each connection would see an empty one.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TestSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    def get_test_db() -> Iterator[Session]:
        """Same as app.database.get_db, but using the in-memory database."""
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    # Every endpoint that asks for get_db now receives get_test_db instead.
    app.dependency_overrides[get_db] = get_test_db

    test_client = TestClient(app)
    yield test_client

    # The test has finished: put the real database dependency back.
    app.dependency_overrides.clear()
