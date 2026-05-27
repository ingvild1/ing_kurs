"""Pytest fixtures for backend tests.

Provides an in-memory SQLite engine and a FastAPI TestClient with the
`get_db` dependency overridden so tests never touch the on-disk
`workshop.db` at the repo root.

Two non-obvious choices to preserve when editing:

1. `StaticPool` + `check_same_thread=False`: SQLite `:memory:` databases
   are per-connection, so the pool must hand out the same connection to
   every request within a test, including across threads (TestClient
   uses a worker thread).
2. Plain `TestClient(app)` instead of `with TestClient(app) as client`:
   the `with` form runs the FastAPI lifespan, which calls
   `Base.metadata.create_all` against the real engine and silently
   creates an empty `workshop.db` file. The in-memory engine fixture
   already creates the tables tests need.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def engine():
    # Function-scoped so each test gets a fresh in-memory DB with no row
    # leakage from earlier tests. StaticPool ensures the single in-memory
    # connection is shared across threads within one test.
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture()
def db_session(engine):
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    # Plain TestClient (no `with`) — avoids triggering the app lifespan, which
    # would call Base.metadata.create_all against the real engine and create
    # an empty workshop.db file at the repo root. The in-memory engine fixture
    # already creates the tables tests need.
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()
