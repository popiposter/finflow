"""API tests for normalized error responses."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.api


class TestErrorContract:
    async def test_auth_me_requires_normalized_error_payload(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.get("/api/v1/auth/me")

        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "authentication_required"
        assert data["error"]["message"] == "Not authenticated"
        assert data["error"]["fields"] == {}

    async def test_register_validation_uses_field_map(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "12345678"},
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "validation_error"
        assert data["error"]["fields"]["email"]
