"""PostgreSQL test fixtures using Testcontainers.

This module provides centralized fixtures for DB-dependent tests that require
a real PostgreSQL database. Uses Testcontainers for local development and
is designed to work with GitHub Actions PostgreSQL service containers in CI.

Fixture lifecycle:
- postgres_container: Starts/stops a PostgreSQL container (session-scoped)
- db_url: Yields the database URL for tests
- db_engine: Creates an async engine connected to test DB
- db_session: Provides isolated async DB sessions for tests

Unified behavior:
- If DATABASE_URL environment variable is set, use it directly
- Otherwise, use Testcontainers PostgreSQL (local development)
"""

import os
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer


def _get_database_url() -> str:
    """Get database URL from environment or Testcontainers.

    Returns DATABASE_URL if set, otherwise uses Testcontainers.
    Testcontainers defaults to psycopg2 driver, but we override to use
    asyncpg to match the project's async SQLAlchemy configuration.
    """
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]

    # Use Testcontainers for local development
    container = PostgresContainer("postgres:16-alpine", driver="asyncpg")
    container.start()
    return str(container.get_connection_url())


@pytest.fixture(scope="session")
def database_url() -> str:
    """Get the database URL for tests.

    Returns DATABASE_URL if set in environment, otherwise starts
    a Testcontainers PostgreSQL instance and returns its URL.

    Returns:
        The database URL as a string.
    """
    return _get_database_url()


@pytest.fixture
async def db_engine(database_url: str) -> AsyncGenerator[AsyncEngine, None]:
    """Create an async SQLAlchemy engine connected to the test database.

    Args:
        database_url: The database URL (from environment or Testcontainers).

    Yields:
        AsyncEngine: The configured async engine.
    """
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_size=5,
        max_overflow=2,
        pool_pre_ping=True,
    )

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def db_session(
    db_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated async database session for tests.

    Each test gets a new session with automatic rollback to ensure isolation.

    Args:
        db_engine: The async engine connected to test DB.

    Yields:
        AsyncSession: A database session that auto-rolls back after use.
    """
    # Create session factory
    async_session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_factory() as session:
        try:
            yield session
        finally:
            # Rollback any changes to keep test isolation
            await session.rollback()


@pytest.fixture
async def clean_db(db_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    """Provide a clean database schema for tests.

    This fixture creates the schema before the test and drops it afterward.
    Use this when tests need to create their own tables.

    Args:
        db_engine: The async engine connected to test DB.

    Yields:
        None: After the test completes.
    """
    from app.db.base import Base

    async with db_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield
    finally:
        async with db_engine.begin() as conn:
            # Drop all tables after test
            await conn.run_sync(Base.metadata.drop_all)
