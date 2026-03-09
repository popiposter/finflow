"""API tests for planned payments endpoints.

These tests verify CRUD operations and transaction generation:
- POST /api/v1/planned-payments - Create
- GET /api/v1/planned-payments - List
- GET /api/v1/planned-payments/{id} - Get
- PUT /api/v1/planned-payments/{id} - Update
- DELETE /api/v1/planned-payments/{id} - Delete (soft)
- POST /api/v1/planned-payments/generate - Generate transactions
"""

from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.db import async_session_factory

pytestmark = pytest.mark.api


@pytest.mark.api
class TestCreatePlannedPayment:
    """Tests for POST /api/v1/planned-payments."""

    async def test_create_planned_payment_success(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test successful planned payment creation via API."""
        # Register user
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "createuser@example.com", "password": "SecurePass123!"},
        )
        assert register_response.status_code == 201
        user_data = register_response.json()
        user_id = user_data["id"]

        # Get access token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "createuser@example.com", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]

        # Create account directly in DB (since accounts endpoint is removed)
        from app.models.types import AccountType
        from app.repositories.account_repository import AccountRepository

        async with async_session_factory() as session:
            account_repo = AccountRepository(session)
            account = await account_repo.create(
                user_id=user_id,
                name="Test Checking Account",
                type_=AccountType.CHECKING,
            )
            account.currency_code = "USD"
            account.current_balance = Decimal("0.00")
            await account_repo.update(account)
            await session.commit()

        # Create planned payment via API
        response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account.id),
                "amount": "1500.00",
                "description": "Monthly rent",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
                "is_active": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Monthly rent"
        assert data["recurrence"] == "monthly"
        assert data["amount"] == "1500.00"
        assert data["is_active"] is True

    async def test_create_planned_payment_with_category(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test creating planned payment with category reference via API."""
        # Register user
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "categoryuser@example.com", "password": "SecurePass123!"},
        )
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]

        # Get access token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "categoryuser@example.com", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]

        # Create account and category directly in DB
        from app.models.types import AccountType, CategoryType
        from app.repositories.account_repository import AccountRepository
        from app.repositories.category_repository import CategoryRepository

        async with async_session_factory() as session:
            account_repo = AccountRepository(session)
            account = await account_repo.create(
                user_id=user_id,
                name="Test Account",
                type_=AccountType.CHECKING,
            )
            account.currency_code = "USD"
            account.current_balance = Decimal("0.00")
            await account_repo.update(account)

            category_repo = CategoryRepository(session)
            category = await category_repo.create(
                user_id=user_id,
                name="Housing",
                type_=CategoryType.EXPENSE,
            )
            await session.commit()

        # Create planned payment via API
        response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account.id),
                "category_id": str(category.id),
                "amount": "500.00",
                "recurrence": "monthly",
                "start_date": "2024-02-01",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["category_id"] == str(category.id)

    async def test_create_planned_payment_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """Test creating planned payment without authentication."""
        response = await async_client.post(
            "/api/v1/planned-payments",
            json={
                "account_id": "12345678-1234-1234-1234-123456789012",
                "amount": "1500.00",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
            },
        )

        assert response.status_code == 401


@pytest.mark.api
class TestListPlannedPayments:
    """Tests for GET /api/v1/planned-payments."""

    async def test_list_planned_payments_empty(self, async_client: AsyncClient) -> None:
        """Test listing planned payments when none exist."""
        # Create user
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
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


@pytest.mark.api
class TestGetPlannedPayment:
    """Tests for GET /api/v1/planned-payments/{id}."""

    async def test_get_planned_payment_not_found(
        self, async_client: AsyncClient
    ) -> None:
        """Test getting a non-existent planned payment."""
        # Create user
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "getnotfound@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "getnotfound@example.com", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]

        fake_id = "12345678-1234-1234-1234-123456789012"
        response = await async_client.get(
            f"/api/v1/planned-payments/{fake_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 404


@pytest.mark.api
class TestUpdatePlannedPayment:
    """Tests for PUT /api/v1/planned-payments/{id}."""

    async def test_update_planned_payment_not_found(
        self, async_client: AsyncClient
    ) -> None:
        """Test updating a non-existent planned payment."""
        # Create user
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "updatenotfound@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "updatenotfound@example.com", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]

        fake_id = "12345678-1234-1234-1234-123456789012"
        response = await async_client.put(
            f"/api/v1/planned-payments/{fake_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": "22345678-1234-1234-1234-123456789012",
                "amount": "1000.00",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
            },
        )

        assert response.status_code == 404


@pytest.mark.api
class TestDeletePlannedPayment:
    """Tests for DELETE /api/v1/planned-payments/{id}."""

    async def test_delete_planned_payment_not_found(
        self, async_client: AsyncClient
    ) -> None:
        """Test deleting a non-existent planned payment."""
        # Create user
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "deletenotfound@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "deletenotfound@example.com", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]

        fake_id = "12345678-1234-1234-1234-123456789012"
        response = await async_client.delete(
            f"/api/v1/planned-payments/{fake_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 404


@pytest.mark.api
class TestGenerateTransactions:
    """Tests for POST /api/v1/planned-payments/generate."""

    async def test_generate_transactions_empty(self, async_client: AsyncClient) -> None:
        """Test generation when no payments are due."""
        # Create user
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "generateuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "generateuser@example.com", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]

        response = await async_client.post(
            "/api/v1/planned-payments/generate",
            headers={"Authorization": f"Bearer {access_token}"},
            json={},  # No body needed for generation
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
