"""Test configuration and fixtures for async API tests."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient
from starlette.testclient import TestClient

from app.api.v1.router import router
from app.db import engine, sync_engine
from app.db.base import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for the entire test session.

    This ensures all async operations use the same event loop,
    avoiding issues with connection pool and asyncpg.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db() -> None:
    """Create and clean database tables for testing once per session.

    Uses sync engine to avoid event loop issues with asyncpg.
    """
    Base.metadata.create_all(bind=sync_engine)
    yield
    # Drop all tables in correct order (reverse of creation)
    # To handle foreign key dependencies, we drop in this order:
    # refresh_sessions -> api_tokens -> users
    from sqlalchemy import text

    with sync_engine.begin() as conn:
        conn.execute(text('DROP TABLE IF EXISTS refresh_sessions CASCADE'))
        conn.execute(text('DROP TABLE IF EXISTS api_tokens CASCADE'))
        conn.execute(text('DROP TABLE IF EXISTS users CASCADE'))


@pytest.fixture
def app():
    """Create a FastAPI application instance for testing.

    Uses the router from the app which includes all auth endpoints.
    """
    from fastapi import FastAPI

    test_app = FastAPI(lifespan=router.lifespan_context)
    test_app.include_router(router)

    yield test_app


@pytest.fixture
def client(app) -> TestClient:
    """Create a synchronous test client using httpx TestClient.

    Args:
        app: FastAPI application instance.

    Returns:
        TestClient for making sync HTTP requests.
    """
    return TestClient(app=app)


@pytest.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client using httpx.

    Uses ASGI transport for direct app testing without network overhead.
    """
    from httpx import ASGITransport

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver.local",
    ) as client:
        yield client


@pytest.fixture(autouse=True)
async def clean_database():
    """Clean all tables and reset async engine pool between tests.

    Uses sync engine for table cleanup to avoid event loop issues.
    Also resets the async engine's pool to prevent stale connections.
    """
    from sqlalchemy import text

    # Get all table names and truncate them using sync engine
    with sync_engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name != '_alembic_revision'
                """
            )
        )
        tables = [row[0] for row in result.fetchall()]

        # Truncate all tables in correct order (respecting foreign keys)
        for table in reversed(tables):
            conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE;'))

        conn.commit()

    # Reset the async engine's pool to prevent stale connections
    # This ensures each test starts with a fresh connection pool
    await engine.dispose()
