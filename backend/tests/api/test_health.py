"""API tests for health endpoints."""

import pytest
from starlette.testclient import TestClient


pytestmark = pytest.mark.api


def test_scheduler_health_endpoint(client: TestClient) -> None:
    """Test scheduler health endpoint exposes running scheduler state."""
    response = client.get("/api/v1/health/scheduler")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["next_run"] is not None
