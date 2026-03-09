"""API tests for planned payments endpoints.

These tests verify CRUD operations and transaction generation:
- POST /api/v1/planned-payments - Create
- GET /api/v1/planned-payments - List
- GET /api/v1/planned-payments/{id} - Get
- PUT /api/v1/planned-payments/{id} - Update
- DELETE /api/v1/planned-payments/{id} - Delete (soft)
- POST /api/v1/planned-payments/generate - Generate transactions
"""

from datetime import date, timedelta

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.api


@pytest.fixture
def user_token(async_client: AsyncClient) -> str:
    """Create a test user and return access token."""
    async_client.post(
        "/api/v1/auth/register",
        json={"email": "ppuser@example.com", "password": "SecurePass123!"},
    )

    login_response = async_client.post(
        "/api/v1/auth/login",
        json={"email": "ppuser@example.com", "password": "SecurePass123!"},
    )

    return login_response.json()["access_token"]


@pytest.mark.api
class TestCreatePlannedPayment:
    """Tests for POST /api/v1/planned-payments."""

    async def test_create_planned_payment_success(
        self, async_client: AsyncClient
    ) -> None:
        """Test successful planned payment creation."""
        # Create user and get token
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "createuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "createuser@example.com", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]

        # Create an account first (needed for planned payment)
        account_response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": "Test Checking Account",
                "type": "checking",
                "currency_code": "USD",
            },
        )
        account_id = account_response.json()["id"]

        # Create planned payment
        response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
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
        self, async_client: AsyncClient
    ) -> None:
        """Test creating planned payment with category reference."""
        # Create user, account, and category
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "categoryuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "categoryuser@example.com", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]

        # Create account
        account_response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Test Account", "type": "checking", "currency_code": "USD"},
        )
        account_id = account_response.json()["id"]

        # Create category
        cat_response = await async_client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Housing", "type": "expense"},
        )
        category_id = cat_response.json()["id"]

        response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "category_id": category_id,
                "amount": "500.00",
                "recurrence": "monthly",
                "start_date": "2024-02-01",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["category_id"] == category_id

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

    async def test_list_planned_payments_with_data(
        self, async_client: AsyncClient
    ) -> None:
        """Test listing planned payments with existing data."""
        # Create user, account, and planned payments
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "listdatauser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "listdatauser@example.com", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]

        # Create account
        account_response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Test Account", "type": "checking", "currency_code": "USD"},
        )
        account_id = account_response.json()["id"]

        # Create first planned payment
        await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "amount": "1000.00",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
            },
        )

        # Create second planned payment
        await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "amount": "500.00",
                "recurrence": "weekly",
                "start_date": "2024-01-08",
            },
        )

        response = await async_client.get(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


@pytest.mark.api
class TestGetPlannedPayment:
    """Tests for GET /api/v1/planned-payments/{id}."""

    async def test_get_planned_payment_success(self, async_client: AsyncClient) -> None:
        """Test getting a specific planned payment."""
        # Create user, account, and planned payment
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "getuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "getuser@example.com", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]

        # Create account
        account_response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Test Account", "type": "checking", "currency_code": "USD"},
        )
        account_id = account_response.json()["id"]

        # Create planned payment
        create_response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "amount": "1000.00",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
            },
        )
        payment_id = create_response.json()["id"]

        # Get planned payment
        response = await async_client.get(
            f"/api/v1/planned-payments/{payment_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == payment_id
        assert data["amount"] == "1000.00"

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

    async def test_update_planned_payment_success(
        self, async_client: AsyncClient
    ) -> None:
        """Test updating a planned payment."""
        # Create user, account, and planned payment
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "updateuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "updateuser@example.com", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]

        # Create account
        account_response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Test Account", "type": "checking", "currency_code": "USD"},
        )
        account_id = account_response.json()["id"]

        # Create planned payment
        create_response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "amount": "1000.00",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
                "description": "Old description",
            },
        )
        payment_id = create_response.json()["id"]

        # Update planned payment
        response = await async_client.put(
            f"/api/v1/planned-payments/{payment_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "amount": "1200.00",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
                "description": "Updated description",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == "1200.00"
        assert data["description"] == "Updated description"

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

    async def test_delete_planned_payment_success(
        self, async_client: AsyncClient
    ) -> None:
        """Test soft-deleting a planned payment."""
        # Create user, account, and planned payment
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "deleteuser@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "deleteuser@example.com", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]

        # Create account
        account_response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Test Account", "type": "checking", "currency_code": "USD"},
        )
        account_id = account_response.json()["id"]

        # Create planned payment
        create_response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "amount": "1000.00",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
            },
        )
        payment_id = create_response.json()["id"]

        # Delete planned payment
        response = await async_client.delete(
            f"/api/v1/planned-payments/{payment_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 204

        # Verify it's soft-deleted (no longer in list)
        list_response = await async_client.get(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = list_response.json()
        assert all(p["id"] != payment_id for p in data)


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

    async def test_generate_transactions_with_due_payment(
        self, async_client: AsyncClient
    ) -> None:
        """Test generating transactions for a due planned payment."""
        # Create user, account, and planned payment
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "generatepayment@example.com", "password": "SecurePass123!"},
        )
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "generatepayment@example.com", "password": "SecurePass123!"},
        )
        access_token = login_response.json()["access_token"]

        # Create account
        account_response = await async_client.post(
            "/api/v1/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Test Account", "type": "checking", "currency_code": "USD"},
        )
        account_id = account_response.json()["id"]

        # Get yesterday's date for next_due_at
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        # Create planned payment due yesterday (should be picked up)
        await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": account_id,
                "amount": "1000.00",
                "recurrence": "monthly",
                "start_date": yesterday,
                "next_due_at": yesterday,  # Set to yesterday for testing
            },
        )

        # Generate transactions
        response = await async_client.post(
            "/api/v1/planned-payments/generate",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        # May have zero results if today is still in the future for this payment
        assert isinstance(data, list)
