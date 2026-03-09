"""API tests for planned payments endpoints.

These tests verify CRUD operations, transaction generation, and execution flow:
- POST /api/v1/planned-payments - Create
- GET /api/v1/planned-payments - List
- GET /api/v1/planned-payments/{id} - Get
- PUT /api/v1/planned-payments/{id} - Update
- DELETE /api/v1/planned-payments/{id} - Delete (soft)
- POST /api/v1/planned-payments/generate - Generate transactions
- POST /api/v1/planned-payments/execute - Execution flow (idempotent, scheduler-facing)
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


@pytest.mark.api
class TestExecuteDuePayments:
    """Tests for POST /api/v1/planned-payments/execute.

    These tests verify the scheduler-facing execution flow:
    - Create a payment and execute for due date
    - Verify transactions are created
    - Verify idempotent behavior on re-execution
    - Verify no-op when nothing is due
    """

    async def test_execute_creates_transaction(
        self,
        async_client: AsyncClient,
        user_with_account_category: dict,
    ) -> None:
        """Test that execute creates a transaction for a due payment."""
        user_id = user_with_account_category["user_id"]
        account_id = user_with_account_category["account_id"]
        category_id = user_with_account_category["category_id"]
        access_token = user_with_account_category["access_token"]

        # Create a planned payment with today as due date
        today = "2024-01-15"
        response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account_id),
                "category_id": str(category_id),
                "amount": "1000.00",
                "description": "Monthly subscription",
                "recurrence": "monthly",
                "start_date": today,
                "next_due_at": today,  # Due today
                "is_active": True,
            },
        )
        assert response.status_code == 201
        payment_id = response.json()["id"]

        # Execute for today
        execute_response = await async_client.post(
            "/api/v1/planned-payments/execute",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"as_of_date": today},
        )

        assert execute_response.status_code == 200
        data = execute_response.json()

        # Verify summary structure
        assert "total_processed" in data
        assert "total_generated" in data
        assert "skipped_occurrences" in data
        assert "details" in data

        assert data["total_processed"] == 1
        assert data["total_generated"] == 1
        assert data["skipped_occurrences"] == 0

        # Verify details
        assert len(data["details"]) == 1
        detail = data["details"][0]
        assert detail["planned_payment_id"] == payment_id
        assert len(detail["generated_transactions"]) == 1
        assert detail["next_due_at"] == "2024-02-15"  # Next month

    async def test_execute_idempotent_on_repeat(
        self,
        async_client: AsyncClient,
        user_with_account_category: dict,
    ) -> None:
        """Test that re-executing doesn't duplicate transactions."""
        user_id = user_with_account_category["user_id"]
        account_id = user_with_account_category["account_id"]
        category_id = user_with_account_category["category_id"]
        access_token = user_with_account_category["access_token"]

        today = "2024-01-15"

        # Create a planned payment
        response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account_id),
                "category_id": str(category_id),
                "amount": "1000.00",
                "description": "Monthly subscription",
                "recurrence": "monthly",
                "start_date": today,
                "next_due_at": today,
                "is_active": True,
            },
        )
        assert response.status_code == 201

        # First execution
        exec1 = await async_client.post(
            "/api/v1/planned-payments/execute",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"as_of_date": today},
        )
        assert exec1.status_code == 200
        first_result = exec1.json()
        first_transaction_id = first_result["details"][0]["generated_transactions"][0]

        # Second execution (same date) - should be idempotent
        exec2 = await async_client.post(
            "/api/v1/planned-payments/execute",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"as_of_date": today},
        )
        assert exec2.status_code == 200
        second_result = exec2.json()

        # Should show no new transactions generated (idempotent)
        assert second_result["total_generated"] == 0

        # The behavior depends on whether the payment is still due:
        # - If payment was updated (next_due_at changed), details will be empty
        # - If payment is still due, details will show skipped_occurrences
        # Both behaviors are valid for idempotency
        assert second_result["total_processed"] in (0, 1)

    async def test_execute_noop_when_not_due(
        self,
        async_client: AsyncClient,
        user_with_account_category: dict,
    ) -> None:
        """Test that execute returns empty when nothing is due."""
        user_id = user_with_account_category["user_id"]
        account_id = user_with_account_category["account_id"]
        category_id = user_with_account_category["category_id"]
        access_token = user_with_account_category["access_token"]

        today = "2024-01-15"
        future_date = "2024-02-01"

        # Create a planned payment with future due date
        response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account_id),
                "category_id": str(category_id),
                "amount": "1000.00",
                "description": "Monthly subscription",
                "recurrence": "monthly",
                "start_date": today,
                "next_due_at": future_date,  # Not due yet
                "is_active": True,
            },
        )
        assert response.status_code == 201

        # Execute for today (before due date)
        execute_response = await async_client.post(
            "/api/v1/planned-payments/execute",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"as_of_date": today},
        )

        assert execute_response.status_code == 200
        data = execute_response.json()

        assert data["total_processed"] == 0
        assert data["total_generated"] == 0
        assert len(data["details"]) == 0

    async def test_execute_unauthorized(self, async_client: AsyncClient) -> None:
        """Test execute endpoint without authentication."""
        response = await async_client.post(
            "/api/v1/planned-payments/execute",
            json={"as_of_date": "2024-01-15"},
        )

        assert response.status_code == 401
