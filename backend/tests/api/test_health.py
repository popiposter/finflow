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


def test_health_includes_request_id_header(client: TestClient) -> None:
    """Health responses should carry a request ID header."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_integrations_health_endpoint(client: TestClient) -> None:
    """Test integrations health exposes safe public config state."""
    response = client.get("/api/v1/health/integrations")

    assert response.status_code == 200
    data = response.json()
    assert "telegram" in data
    assert "ollama" in data
    assert "commands" in data["telegram"]
    assert "model" in data["ollama"]
