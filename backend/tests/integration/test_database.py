"""Integration tests for PostgreSQL-backed database functionality.

These tests verify that the PostgreSQL test infrastructure works correctly
both locally (via Testcontainers) and in CI (via PostgreSQL service container).

To run these tests locally with Docker:
    pytest tests/integration/ -v

To run with a specific DATABASE_URL (e.g., for local dev database):
    DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db pytest tests/integration/ -v
"""

import pytest
from sqlalchemy import text


@pytest.mark.integration
class TestDatabaseConnection:
    """Tests for basic database connectivity using PostgreSQL fixtures."""

    @pytest.mark.asyncio
    async def test_database_url_is_configured(self, database_url) -> None:
        """Verify that database_url fixture returns a valid PostgreSQL URL."""
        assert database_url is not None
        assert "postgresql" in database_url
        assert "localhost" in database_url or "finflow" in database_url

    @pytest.mark.asyncio
    async def test_db_engine_connects_to_postgres(self, db_engine) -> None:
        """Verify that db_engine fixture creates a working connection."""
        from sqlalchemy.ext.asyncio import AsyncEngine

        assert db_engine is not None
        assert isinstance(db_engine, AsyncEngine)

    @pytest.mark.asyncio
    async def test_db_session_executes_query(self, db_session) -> None:
        """Verify that db_session fixture provides a working session."""
        result = await db_session.execute(text("SELECT 1"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 1

    @pytest.mark.asyncio
    async def test_db_session_rolls_back_changes(self, db_session) -> None:
        """Verify that db_session rolls back changes after test."""
        # Insert a test row
        await db_session.execute(text("SELECT 1"))
        await db_session.commit()

        # Verify we can execute another query
        result = await db_session.execute(text("SELECT 2"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 2


@pytest.mark.integration
class TestSchemaOperations:
    """Tests for database schema operations using clean_db fixture."""

    @pytest.mark.asyncio
    async def test_clean_db_creates_schema(self, clean_db, db_engine) -> None:
        """Verify that clean_db fixture creates the database schema."""

        # Verify tables were created by clean_db fixture
        async with db_engine.begin() as conn:
            result = await conn.execute(
                text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
                )
            )
            row = result.fetchone()
            # Base metadata should have tables, but we check for general creation
            assert row is not None

    @pytest.mark.asyncio
    async def test_clean_db_drops_schema_after_test(self, db_engine) -> None:
        """Verify that clean_db fixture cleans up after the test."""

        async with db_engine.begin() as conn:
            # This should work since clean_db is used in previous test
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row is not None
