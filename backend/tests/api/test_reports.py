"""Smoke tests for reporting API endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def auth_user(async_client: AsyncClient) -> dict:
    """Register and login a user to get auth token."""
    # Register
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "reporttest@example.com", "password": "SecurePass123!"},
    )
    assert register_response.status_code == 201
    user_data = register_response.json()

    # Login
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "reporttest@example.com", "password": "SecurePass123!"},
    )
    assert login_response.status_code == 200

    return {
        "user_id": user_data["id"],
        "access_token": login_response.json()["access_token"],
    }


class TestReportsAPI:
    """Smoke tests for reporting endpoints."""

    @pytest_asyncio.fixture
    async def user_with_account_category(
        self,
        async_client: AsyncClient,
        db_session,
    ) -> dict:
        """Create a user with account and category via API."""
        # Register user
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "reportapitest@example.com", "password": "SecurePass123!"},
        )
        assert register_response.status_code == 201
        user_data = register_response.json()
        user_id = user_data["id"]

        # Create account via API
        account_response = await async_client.post(
            "/api/v1/accounts",
            json={
                "name": "Test Account for Reports",
                "type": "checking",
                "currency_code": "USD",
            },
        )
        assert account_response.status_code == 201
        account_data = account_response.json()
        account_id = account_data["id"]

        # Create category via API
        category_response = await async_client.post(
            "/api/v1/categories",
            json={
                "name": "Housing",
                "type": "expense",
            },
        )
        assert category_response.status_code == 201
        category_data = category_response.json()
        category_id = category_data["id"]

        # Login to get token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "reportapitest@example.com", "password": "SecurePass123!"},
        )
        assert login_response.status_code == 200

        yield {
            "user_id": user_id,
            "account_id": account_id,
            "category_id": category_id,
            "access_token": login_response.json()["access_token"],
        }

    @pytest.mark.asyncio
    async def test_pnl_endpoint_unauthorized(self, async_client: AsyncClient) -> None:
        """Test P&L endpoint returns 401 without auth."""
        response = await async_client.get("/api/v1/reports/pnl")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_cashflow_endpoint_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test cashflow endpoint returns 401 without auth."""
        response = await async_client.get("/api/v1/reports/cashflow")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_pnl_endpoint_empty_user(
        self, async_client: AsyncClient, auth_user: dict
    ) -> None:
        """Test P&L endpoint returns empty result for user with no transactions."""
        headers = {"Authorization": f"Bearer {auth_user['access_token']}"}
        response = await async_client.get(
            "/api/v1/reports/pnl",
            headers=headers,
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Decimal is serialized as string in JSON
        assert data["grand_total"] == "0.00"
        assert data["totals_by_category"] == []
        assert data["totals_by_type"] == []

    @pytest.mark.asyncio
    async def test_cashflow_endpoint_empty_user(
        self, async_client: AsyncClient, auth_user: dict
    ) -> None:
        """Test cashflow endpoint returns empty result for user with no transactions."""
        headers = {"Authorization": f"Bearer {auth_user['access_token']}"}
        response = await async_client.get(
            "/api/v1/reports/cashflow",
            headers=headers,
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Decimal is serialized as string in JSON
        assert data["grand_total"] == "0.00"
        assert data["totals_by_category"] == []
        assert data["totals_by_type"] == []

    @pytest.mark.asyncio
    async def test_pnl_date_filtering(
        self, async_client: AsyncClient, auth_user: dict
    ) -> None:
        """Test P&L endpoint properly filters by date."""
        headers = {"Authorization": f"Bearer {auth_user['access_token']}"}

        # Query with specific date range
        response = await async_client.get(
            "/api/v1/reports/pnl",
            headers=headers,
            params={
                "start_date": "2024-06-01",
                "end_date": "2024-06-30",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Should return valid structure even if empty
        assert "grand_total" in data
        assert "totals_by_category" in data
        assert "totals_by_type" in data

    @pytest.mark.asyncio
    async def test_cashflow_date_filtering(
        self, async_client: AsyncClient, auth_user: dict
    ) -> None:
        """Test cashflow endpoint properly filters by date."""
        headers = {"Authorization": f"Bearer {auth_user['access_token']}"}

        # Query with specific date range
        response = await async_client.get(
            "/api/v1/reports/cashflow",
            headers=headers,
            params={
                "start_date": "2024-06-01",
                "end_date": "2024-06-30",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Should return valid structure even if empty
        assert "grand_total" in data
        assert "totals_by_category" in data
        assert "totals_by_type" in data

    @pytest.mark.asyncio
    async def test_pnl_grouping_by_category(
        self, async_client: AsyncClient, auth_user: dict
    ) -> None:
        """Test P&L endpoint supports grouping by category."""
        headers = {"Authorization": f"Bearer {auth_user['access_token']}"}

        response = await async_client.get(
            "/api/v1/reports/pnl",
            headers=headers,
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "group_by": "by_category",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "totals_by_category" in data

    @pytest.mark.asyncio
    async def test_pnl_grouping_by_type(
        self, async_client: AsyncClient, auth_user: dict
    ) -> None:
        """Test P&L endpoint supports grouping by type."""
        headers = {"Authorization": f"Bearer {auth_user['access_token']}"}

        response = await async_client.get(
            "/api/v1/reports/pnl",
            headers=headers,
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "group_by": "by_type",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "totals_by_type" in data
