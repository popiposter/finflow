"""Test configuration and fixtures."""

import asyncio

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> TestClient:
    """Create test client fixture."""
    return TestClient(app)
