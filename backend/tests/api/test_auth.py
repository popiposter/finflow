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
from httpx import AsyncClient

pytestmark = pytest.mark.api
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
        # Register first user
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "duplicate@example.com", "password": "SecurePass123!"},
        )

        # Try to register again with same email
        response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "duplicate@example.com", "password": "AnotherPass123!"},
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

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
        # First register a user
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "loginuser@example.com", "password": "SecurePass123!"},
        )

        # Login
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "loginuser@example.com", "password": "SecurePass123!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Check that cookies were set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    async def test_login_invalid_credentials(self, async_client: AsyncClient) -> None:
        """Test login with invalid credentials."""
        # Register a user first
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "loginuser@example.com", "password": "SecurePass123!"},
        )

        # Login with wrong password
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "loginuser@example.com", "password": "WrongPassword!"},
        )

        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()

    async def test_login_user_not_found(self, async_client: AsyncClient) -> None:
        """Test login with non-existent user."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "AnyPass123!"},
        )

        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()


@pytest.mark.api
class TestRefreshEndpoint:
    """Tests for POST /api/v1/auth/refresh."""

    async def test_refresh_success(self, async_client: AsyncClient) -> None:
        """Test successful token refresh."""
        # Register and login
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

        # Refresh tokens - set cookie directly on client
        async_client.cookies.set("refresh_token", refresh_token)

        response = await async_client.post("/api/v1/auth/refresh")

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

        # New cookies should be set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    async def test_refresh_missing_token(self, async_client: AsyncClient) -> None:
        """Test refresh without refresh token."""
        response = await async_client.post("/api/v1/auth/refresh")

        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()

    async def test_refresh_token_rotation(self, async_client: AsyncClient) -> None:
        """Test that old refresh token is invalidated after rotation."""
        from fastapi import FastAPI
        from httpx import ASGITransport

        from app.api.v1.router import router

        # First, complete normal flow on main client
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "rotationuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "rotationuser@example.com", "password": "SecurePass123!"},
        )

        # Get the initial refresh token before rotation
        refresh_token = login_response.cookies.get("refresh_token")
        assert refresh_token is not None
        print(f"\nRefresh token from login: {refresh_token[:50]}...")
        print(f"Client cookies after login: {repr(async_client.cookies)}")

        # First refresh - should succeed with current client cookies
        response = await async_client.post("/api/v1/auth/refresh")
        print(f"First refresh status: {response.status_code}, body: {response.json()}")
        assert response.status_code == 200

        # Create a NEW client for replay attack test
        # This ensures we test with only the OLD token, not mixed with new cookies
        replay_app = FastAPI(lifespan=router.lifespan_context)
        replay_app.include_router(router)

        async with AsyncClient(
            transport=ASGITransport(app=replay_app),
            base_url="http://testserver.local",
        ) as replay_client:
            # Set ONLY the OLD refresh token on the replay client
            replay_client.cookies.set("refresh_token", refresh_token)

            # Try to use the OLD refresh token - should fail because it was revoked
            response = await replay_client.post("/api/v1/auth/refresh")
            assert response.status_code == 401
            assert "invalid refresh token" in response.json()["detail"].lower()


@pytest.mark.api
class TestLogoutEndpoint:
    """Tests for POST /api/v1/auth/logout."""

    async def test_logout_success(self, async_client: AsyncClient) -> None:
        """Test successful logout."""
        from fastapi import FastAPI
        from httpx import ASGITransport

        from app.api.v1.router import router

        # Register and login
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "logoutuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "logoutuser@example.com", "password": "SecurePass123!"},
        )

        # Get the refresh token before logout
        refresh_token = login_response.cookies.get("refresh_token")
        assert refresh_token is not None

        # Logout
        logout_response = await async_client.post("/api/v1/auth/logout")

        assert logout_response.status_code == 200
        data = logout_response.json()
        assert data["message"] == "Logged out successfully"

        # Verify refresh token is invalidated on server using a NEW client
        # This ensures we test with only the OLD token, not mixed with new cookies
        replay_app = FastAPI(lifespan=router.lifespan_context)
        replay_app.include_router(router)

        async with AsyncClient(
            transport=ASGITransport(app=replay_app),
            base_url="http://testserver.local",
        ) as replay_client:
            # Set ONLY the OLD refresh token on the replay client
            replay_client.cookies.set("refresh_token", refresh_token)

            # Try to use the OLD refresh token - should fail because it was revoked
            response = await replay_client.post("/api/v1/auth/refresh")
            assert response.status_code == 401
            assert "invalid refresh token" in response.json()["detail"].lower()


@pytest.mark.api
class TestMeEndpoint:
    """Tests for GET /api/v1/auth/me."""

    async def test_me_unauthorized(self, async_client: AsyncClient) -> None:
        """Test accessing /me without authentication."""
        response = await async_client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()

    async def test_me_success(self, async_client: AsyncClient) -> None:
        """Test accessing /me with valid token."""
        # Register and login
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "meuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "meuser@example.com", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        # Access /me with Authorization header
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
        assert "invalid access token" in response.json()["detail"].lower()


@pytest.mark.api
class TestApiTokensEndpoints:
    """Tests for POST/GET /api/v1/auth/api-tokens."""

    async def test_create_api_token_success(self, async_client: AsyncClient) -> None:
        """Test creating a new API token."""
        # Register and login
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "apiuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "apiuser@example.com", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        # Create API token
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
        # Register and login
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "listuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "listuser@example.com", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        # List API tokens
        response = await async_client.get(
            "/api/v1/auth/api-tokens",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_create_api_token_unauthorized(self, async_client: AsyncClient) -> None:
        """Test creating API token without authentication."""
        response = await async_client.post(
            "/api/v1/auth/api-tokens",
            json={"name": "My Test Token"},
        )

        assert response.status_code == 401
