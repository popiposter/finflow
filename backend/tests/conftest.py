"""Test configuration and fixtures for backend tests."""

from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import TestClient

import app.models  # noqa: F401
from app.db import Base, async_session_factory, engine
from app.main import app


@pytest.fixture
def client(prepare_database: None) -> Generator[TestClient, None, None]:
    """Create a synchronous test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def prepare_database() -> AsyncGenerator[None, None]:
    """Create database tables for an individual test and drop them afterwards."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def clean_db(prepare_database: None) -> AsyncGenerator[None, None]:
    """Provide a compatibility fixture for DB-backed tests.

    Database isolation is handled by the per-test schema lifecycle in
    ``prepare_database``.
    """
    yield


@pytest_asyncio.fixture
async def db_session(prepare_database: None) -> AsyncGenerator[AsyncSession, None]:
    """Create an async database session for a test."""
    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def async_client(prepare_database: None) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for API tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver.local",
    ) as client:
        yield client
