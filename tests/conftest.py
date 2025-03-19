import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine
from yapml.db import get_session
from yapml.server.webapp import web_app


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine"""
    engine = create_engine(
        "sqlite://",  # In-memory SQLite database
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create a test database session"""
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def client(test_session):
    """Create a test client with the test database session"""

    def override_get_session(request: Request):  # FastAPI Request here
        request.state.session = test_session
        yield test_session

    web_app.dependency_overrides[get_session] = override_get_session

    with TestClient(web_app) as client:
        yield client

    web_app.dependency_overrides.clear()
