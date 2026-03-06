# type: ignore
"""PostgreSQL test fixtures using Testcontainers.

This module provides centralized fixtures for DB-dependent tests that require
a real PostgreSQL database. Uses Testcontainers for local development and
is designed to work with GitHub Actions PostgreSQL service containers in CI.

Fixture lifecycle:
- postgres_container: Starts/stops a PostgreSQL container (session-scoped)
- db_url: Yields the database URL for tests
- db_engine: Creates an async engine connected to test DB
- db_session: Provides isolated async DB sessions for tests
"""

import asyncio
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
async def postgres_container() -> AsyncGenerator[PostgresContainer, None]:
    """Start a PostgreSQL container for DB-dependent tests.

    This fixture is session-scoped to avoid restarting the container for
    every test module, but each test gets an isolated database within it.

    Yields:
        PostgresContainer: The running PostgreSQL container instance.
    """
    container = PostgresContainer("postgres:16-alpine")
    container.start()

    # Wait for PostgreSQL to be ready
    await asyncio.to_thread(container.get_connection_url)

    try:
        yield container
    finally:
        container.stop()


@pytest.fixture
def db_url(postgres_container: PostgresContainer) -> str:
    """Get the database URL for the test PostgreSQL instance.

    Args:
        postgres_container: The running PostgreSQL container.

    Returns:
        The database URL as a string.
    """
    return str(postgres_container.get_connection_url())


@pytest.fixture
def db_url_with_test_db(postgres_container: PostgresContainer) -> str:
    """Get the database URL with a unique test database name.

    Creates a unique database name per test session to ensure isolation.

    Args:
        postgres_container: The running PostgreSQL container.

    Returns:
        The database URL pointing to a unique test database.
    """
    connection_url = postgres_container.get_connection_url()

    # For Testcontainers, the URL format is typically:
    # postgresql+psycopg2://postgres:postgres@localhost:port/postgres
    return connection_url.replace("/postgres", "/test_finflow")


@pytest.fixture
async def db_engine(db_url: str) -> AsyncGenerator[AsyncEngine, None]:
    """Create an async SQLAlchemy engine connected to the test database.

    Args:
        db_url: The database URL from postgres_container fixture.

    Yields:
        AsyncEngine: The configured async engine.
    """
    engine = create_async_engine(
        db_url,
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
    async with db_engine.begin() as conn:
        # Start a transaction that will be rolled back after the test
        await conn.begin()

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
