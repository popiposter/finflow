"""Integration test configuration for DB-dependent tests.

This conftest.py provides fixtures for integration tests that require
a real PostgreSQL database. It imports fixtures from postgres.py and
adds integration-specific fixtures.

To run integration tests:
    pytest tests/integration/ -v

To run with a specific DATABASE_URL (e.g., for CI):
    DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db pytest tests/integration/ -v

To run only unit tests (no DB required):
    pytest tests/unit/ -v

To run all tests:
    pytest tests/ -v
"""

from typing import Any

import pytest

from tests.postgres import (
    clean_db,
    database_url,
    db_engine,
    db_session,
)

__all__ = [
    "clean_db",
    "db_engine",
    "db_session",
    "database_url",
]


def pytest_collection_modifyitems(config: Any, items: list[Any]) -> None:
    """Modify collected test items to add markers based on location.

    - Tests in tests/unit/ are marked as unit tests
    - Tests in tests/integration/ are marked as integration tests
    - Tests in tests/api/ are marked as api tests
    """
    unit_marker = pytest.mark.unit
    integration_marker = pytest.mark.integration
    api_marker = pytest.mark.api

    for item in items:
        # Determine test type based on path
        if "unit" in str(item.fspath):
            item.add_marker(unit_marker)
        elif "integration" in str(item.fspath):
            item.add_marker(integration_marker)
        elif "api" in str(item.fspath):
            item.add_marker(api_marker)


def pytest_configure(config: Any) -> None:
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (no database required)")
    config.addinivalue_line(
        "markers", "integration: Integration tests (require PostgreSQL)"
    )
    config.addinivalue_line("markers", "api: API tests (require FastAPI + PostgreSQL)")
