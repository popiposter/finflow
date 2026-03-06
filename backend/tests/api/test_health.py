"""API tests for health endpoint."""

from starlette.testclient import TestClient

from app.core.config import settings


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint returns expected response."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == settings.app_title
    assert data["version"] == settings.app_version


def test_health_check_returns_json(client: TestClient) -> None:
    """Test health check returns JSON content type."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")


def test_settings_loads_in_test_mode() -> None:
    """Test settings load properly in test mode."""
    assert settings.debug is False
    assert settings.app_title == "FinFlow Backend"
    assert settings.app_version == "0.1.0"
    assert settings.database_url is not None
