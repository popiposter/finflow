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
from starlette.testclient import TestClient


@pytest.mark.api
class TestRegisterEndpoint:
    """Tests for POST /api/v1/auth/register."""

    def test_register_success(self, client: TestClient) -> None:
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "SecurePass123!"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert data["is_active"] is True
        assert "created_at" in data

    def test_register_duplicate_email(self, client: TestClient) -> None:
        """Test registration with existing email."""
        # Register first user
        client.post(
            "/api/v1/auth/register",
            json={"email": "duplicate@example.com", "password": "SecurePass123!"},
        )

        # Try to register again with same email
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "duplicate@example.com", "password": "AnotherPass123!"},
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_missing_email(self, client: TestClient) -> None:
        """Test registration without email."""
        response = client.post(
            "/api/v1/auth/register",
            json={"password": "SecurePass123!"},
        )

        assert response.status_code == 422

    def test_register_missing_password(self, client: TestClient) -> None:
        """Test registration without password."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com"},
        )

        assert response.status_code == 422


@pytest.mark.api
class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login."""

    def test_login_success(self, client: TestClient) -> None:
        """Test successful login."""
        # First register a user
        client.post(
            "/api/v1/auth/register",
            json={"email": "loginuser@example.com", "password": "SecurePass123!"},
        )

        # Login
        response = client.post(
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

    def test_login_invalid_credentials(self, client: TestClient) -> None:
        """Test login with invalid credentials."""
        # Register a user first
        client.post(
            "/api/v1/auth/register",
            json={"email": "loginuser@example.com", "password": "SecurePass123!"},
        )

        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "loginuser@example.com", "password": "WrongPassword!"},
        )

        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()

    def test_login_user_not_found(self, client: TestClient) -> None:
        """Test login with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "AnyPass123!"},
        )

        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()


@pytest.mark.api
class TestRefreshEndpoint:
    """Tests for POST /api/v1/auth/refresh."""

    def test_refresh_success(self, client: TestClient) -> None:
        """Test successful token refresh."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={"email": "refreshuser@example.com", "password": "SecurePass123!"},
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "refreshuser@example.com", "password": "SecurePass123!"},
        )

        refresh_token = login_response.cookies.get("refresh_token")
        assert refresh_token is not None

        # Refresh tokens
        response = client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

        # New cookies should be set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    def test_refresh_missing_token(self, client: TestClient) -> None:
        """Test refresh without refresh token."""
        response = client.post("/api/v1/auth/refresh")

        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()


@pytest.mark.api
class TestLogoutEndpoint:
    """Tests for POST /api/v1/auth/logout."""

    def test_logout_success(self, client: TestClient) -> None:
        """Test successful logout."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={"email": "logoutuser@example.com", "password": "SecurePass123!"},
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "logoutuser@example.com", "password": "SecurePass123!"},
        )

        # Verify cookies are set before logout
        assert "access_token" in login_response.cookies
        assert "refresh_token" in login_response.cookies

        # Logout
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logged out successfully"

        # Verify cookies are cleared
        assert login_response.cookies.get("access_token") == ""
        assert login_response.cookies.get("refresh_token") == ""


@pytest.mark.api
class TestMeEndpoint:
    """Tests for GET /api/v1/auth/me."""

    def test_me_unauthorized(self, client: TestClient) -> None:
        """Test accessing /me without authentication."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()

    def test_me_success(self, client: TestClient) -> None:
        """Test accessing /me with valid token."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={"email": "meuser@example.com", "password": "SecurePass123!"},
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "meuser@example.com", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        # Access /me with Authorization header
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "meuser@example.com"
        assert "id" in data

    def test_me_invalid_token(self, client: TestClient) -> None:
        """Test accessing /me with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401
        assert "invalid access token" in response.json()["detail"].lower()


@pytest.mark.api
class TestApiTokensEndpoints:
    """Tests for POST/GET /api/v1/auth/api-tokens."""

    def test_create_api_token_success(self, client: TestClient) -> None:
        """Test creating a new API token."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={"email": "apiuser@example.com", "password": "SecurePass123!"},
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "apiuser@example.com", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        # Create API token
        response = client.post(
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

    def test_list_api_tokens_empty(self, client: TestClient) -> None:
        """Test listing API tokens when none exist."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={"email": "listuser@example.com", "password": "SecurePass123!"},
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "listuser@example.com", "password": "SecurePass123!"},
        )

        access_token = login_response.json()["access_token"]

        # List API tokens
        response = client.get(
            "/api/v1/auth/api-tokens",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_create_api_token_unauthorized(self, client: TestClient) -> None:
        """Test creating API token without authentication."""
        response = client.post(
            "/api/v1/auth/api-tokens",
            json={"name": "My Test Token"},
        )

        assert response.status_code == 401
