"""API tests for authentication endpoints.

These tests verify that the auth endpoints work correctly:
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- GET /api/v1/auth/me
- POST /api/v1/auth/api-tokens
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

pytestmark = pytest.mark.api


def _error_message(response: AsyncClient | object) -> str:
    data = response.json()
    return data["error"]["message"].lower()


class TestRegisterEndpoint:
    """Tests for POST /api/v1/auth/register."""

    async def test_register_success(self, async_client: AsyncClient) -> None:
        """Test successful user registration."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "SecurePass123!"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert data["is_active"] is True
        assert "created_at" in data

    async def test_register_duplicate_email(self, async_client: AsyncClient) -> None:
        """Test registration with existing email."""
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "duplicate@example.com", "password": "SecurePass123!"},
        )

        response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "duplicate@example.com", "password": "AnotherPass123!"},
        )

        assert response.status_code == 400
        assert "already registered" in _error_message(response)

    async def test_register_missing_email(self, async_client: AsyncClient) -> None:
        """Test registration without email."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={"password": "SecurePass123!"},
        )

        assert response.status_code == 422

    async def test_register_missing_password(self, async_client: AsyncClient) -> None:
        """Test registration without password."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com"},
        )

        assert response.status_code == 422


@pytest.mark.api
class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login."""

    async def test_login_success(self, async_client: AsyncClient) -> None:
        """Test successful login."""
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "loginuser@example.com", "password": "SecurePass123!"},
        )

        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "loginuser@example.com", "password": "SecurePass123!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    async def test_login_invalid_credentials(self, async_client: AsyncClient) -> None:
        """Test login with invalid credentials."""
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "loginuser@example.com", "password": "SecurePass123!"},
        )

        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "loginuser@example.com", "password": "WrongPassword!"},
        )

        assert response.status_code == 401
        assert "invalid credentials" in _error_message(response)

    async def test_login_user_not_found(self, async_client: AsyncClient) -> None:
        """Test login with non-existent user."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "AnyPass123!"},
        )

        assert response.status_code == 401
        assert "invalid credentials" in _error_message(response)


@pytest.mark.api
class TestRefreshEndpoint:
    """Tests for POST /api/v1/auth/refresh."""

    async def test_refresh_success(self, async_client: AsyncClient) -> None:
        """Test successful token refresh."""
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "refreshuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "refreshuser@example.com", "password": "SecurePass123!"},
        )

        refresh_token = login_response.cookies.get("refresh_token")
        assert refresh_token is not None

        async_client.cookies.set("refresh_token", refresh_token)

        response = await async_client.post("/api/v1/auth/refresh")

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    async def test_refresh_missing_token(self, async_client: AsyncClient) -> None:
        """Test refresh without refresh token."""
        response = await async_client.post("/api/v1/auth/refresh")

        assert response.status_code == 401
        assert "not authenticated" in _error_message(response)

    async def test_refresh_token_rotation(self, async_client: AsyncClient) -> None:
        """Test that old refresh token is invalidated after rotation."""
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "rotationuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "rotationuser@example.com", "password": "SecurePass123!"},
        )

        refresh_token = login_response.cookies.get("refresh_token")
        assert refresh_token is not None

        response = await async_client.post("/api/v1/auth/refresh")
        assert response.status_code == 200

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver.local",
        ) as replay_client:
            replay_client.cookies.set("refresh_token", refresh_token)

            response = await replay_client.post("/api/v1/auth/refresh")
            assert response.status_code == 401
            assert "invalid refresh token" in _error_message(response)


@pytest.mark.api
class TestLogoutEndpoint:
    """Tests for POST /api/v1/auth/logout."""

    async def test_logout_success(self, async_client: AsyncClient) -> None:
        """Test successful logout."""
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "logoutuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "logoutuser@example.com", "password": "SecurePass123!"},
        )

        refresh_token = login_response.cookies.get("refresh_token")
        assert refresh_token is not None

        logout_response = await async_client.post("/api/v1/auth/logout")

        assert logout_response.status_code == 200
        data = logout_response.json()
        assert data["message"] == "Logged out successfully"

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver.local",
        ) as replay_client:
            replay_client.cookies.set("refresh_token", refresh_token)

            response = await replay_client.post("/api/v1/auth/refresh")
            assert response.status_code == 401
            assert "invalid refresh token" in _error_message(response)


@pytest.mark.api
class TestMeEndpoint:
    """Tests for GET /api/v1/auth/me."""

    async def test_me_unauthorized(self, async_client: AsyncClient) -> None:
        """Test accessing /me without authentication."""
        response = await async_client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "not authenticated" in _error_message(response)

    async def test_me_success(self, async_client: AsyncClient) -> None:
        """Test accessing /me with valid token."""
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "meuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "meuser@example.com", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "meuser@example.com"
        assert "id" in data

    async def test_me_invalid_token(self, async_client: AsyncClient) -> None:
        """Test accessing /me with invalid token."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401
        assert "invalid access token" in _error_message(response)


@pytest.mark.api
class TestApiTokensEndpoints:
    """Tests for POST/GET /api/v1/auth/api-tokens."""

    async def test_create_api_token_success(self, async_client: AsyncClient) -> None:
        """Test creating a new API token."""
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "apiuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "apiuser@example.com", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        response = await async_client.post(
            "/api/v1/auth/api-tokens",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "My Test Token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My Test Token"
        assert "id" in data
        assert "user_id" in data
        assert data["is_revoked"] is False

    async def test_list_api_tokens_empty(self, async_client: AsyncClient) -> None:
        """Test listing API tokens when none exist."""
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "listuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "listuser@example.com", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        response = await async_client.get(
            "/api/v1/auth/api-tokens",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_create_api_token_unauthorized(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test creating API token without authentication."""
        response = await async_client.post(
            "/api/v1/auth/api-tokens",
            json={"name": "My Test Token"},
        )

        assert response.status_code == 401
