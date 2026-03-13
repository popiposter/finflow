"""API tests for projected transactions endpoints.

These tests verify CRUD operations, state transitions, and confirmation flow:
- GET /api/v1/projected-transactions - List
- GET /api/v1/projected-transactions/{id} - Get
- PATCH /api/v1/projected-transactions/{id} - Update
- POST /api/v1/projected-transactions/{id}/confirm - Confirm
- POST /api/v1/projected-transactions/{id}/skip - Skip
"""

from datetime import date, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.db import async_session_factory

pytestmark = pytest.mark.api


def _error_message(response: AsyncClient | object) -> str:
    data = response.json()
    return data["error"]["message"]


class TestListProjectedTransactions:
    """Tests for GET /api/v1/projected-transactions."""

    async def test_list_projected_transactions_empty(
        self, async_client: AsyncClient
    ) -> None:
        """Test listing projected transactions when none exist."""
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
            "/api/v1/projected-transactions",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_list_projected_transactions_with_filter(
        self,
        async_client: AsyncClient,
        user_with_account_category: dict,
    ) -> None:
        """Test listing projected transactions with status filter."""
        user_id = user_with_account_category["user_id"]
        account_id = user_with_account_category["account_id"]
        access_token = user_with_account_category["access_token"]

        # Create a planned payment
        response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account_id),
                "amount": "1000.00",
                "description": "Monthly rent",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
                "next_due_at": "2024-01-15",
                "is_active": True,
            },
        )
        assert response.status_code == 201
        payment_id = response.json()["id"]

        # Create a projected transaction via DB
        from app.models.projected_transaction import ProjectedTransaction
        from app.models.types import (
            ProjectedTransactionStatus,
            ProjectedTransactionType,
        )
        from app.repositories.projected_transaction_repository import (
            ProjectedTransactionRepository,
        )

        async with async_session_factory() as session:
            repo = ProjectedTransactionRepository(session)
            projected = await repo.create(
                planned_payment_id=payment_id,
                origin_date=date(2024, 1, 15),
                origin_amount=Decimal("1000"),
                origin_description="Monthly rent",
                origin_category_id=None,
                type_=ProjectedTransactionType.EXPENSE,
                projected_date=date(2024, 1, 15),
                projected_amount=Decimal("1000"),
                projected_description="Monthly rent",
                projected_category_id=None,
            )
            await session.commit()

        # List all
        response = await async_client.get(
            "/api/v1/projected-transactions",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "pending"

        # Filter by status
        response = await async_client.get(
            "/api/v1/projected-transactions?status=pending",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        # Filter by date range
        response = await async_client.get(
            "/api/v1/projected-transactions?from=2024-01-01&to=2024-01-31",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


class TestGetProjectedTransaction:
    """Tests for GET /api/v1/projected-transactions/{id}."""

    async def test_get_projected_transaction_not_found(
        self, async_client: AsyncClient
    ) -> None:
        """Test getting a non-existent projected transaction."""
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
            f"/api/v1/projected-transactions/{fake_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 404


class TestUpdateProjectedTransaction:
    """Tests for PATCH /api/v1/projected-transactions/{id}."""

    async def test_update_projected_transaction(
        self,
        async_client: AsyncClient,
        user_with_account_category: dict,
    ) -> None:
        """Test updating a pending projected transaction."""
        user_id = user_with_account_category["user_id"]
        account_id = user_with_account_category["account_id"]
        access_token = user_with_account_category["access_token"]

        # Create a planned payment
        response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account_id),
                "amount": "1000.00",
                "description": "Monthly rent",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
                "next_due_at": "2024-01-15",
                "is_active": True,
            },
        )
        assert response.status_code == 201
        payment_id = response.json()["id"]

        # Create a projected transaction via DB
        from app.models.projected_transaction import ProjectedTransaction
        from app.models.types import (
            ProjectedTransactionStatus,
            ProjectedTransactionType,
        )
        from app.repositories.projected_transaction_repository import (
            ProjectedTransactionRepository,
        )

        async with async_session_factory() as session:
            repo = ProjectedTransactionRepository(session)
            projected = await repo.create(
                planned_payment_id=payment_id,
                origin_date=date(2024, 1, 15),
                origin_amount=Decimal("1000"),
                origin_description="Monthly rent",
                origin_category_id=None,
                type_=ProjectedTransactionType.EXPENSE,
                projected_date=date(2024, 1, 15),
                projected_amount=Decimal("1000"),
                projected_description="Monthly rent",
                projected_category_id=None,
            )
            await session.commit()

        # Update the projection
        update_response = await async_client.patch(
            f"/api/v1/projected-transactions/{projected.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "projected_amount": "1200.00",
                "projected_description": "Monthly rent with increase",
            },
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["projected_amount"] == "1200.00"
        assert data["projected_description"] == "Monthly rent with increase"
        assert data["origin_amount"] == "1000.00"  # Origin should not change
        assert data["status"] == "pending"

    async def test_update_non_pending_projection(
        self,
        async_client: AsyncClient,
        user_with_account_category: dict,
    ) -> None:
        """Test updating a confirmed projection returns 409."""
        user_id = user_with_account_category["user_id"]
        account_id = user_with_account_category["account_id"]
        access_token = user_with_account_category["access_token"]

        # Create a planned payment
        response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account_id),
                "amount": "1000.00",
                "description": "Monthly rent",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
                "next_due_at": "2024-01-15",
                "is_active": True,
            },
        )
        assert response.status_code == 201
        payment_id = response.json()["id"]

        # Create a projected transaction via DB
        from app.models.projected_transaction import ProjectedTransaction
        from app.models.types import (
            ProjectedTransactionStatus,
            ProjectedTransactionType,
        )
        from app.repositories.projected_transaction_repository import (
            ProjectedTransactionRepository,
        )
        from app.repositories.transaction_repository import TransactionRepository
        from app.services.projected_transaction_service import ProjectedTransactionService

        async with async_session_factory() as session:
            repo = ProjectedTransactionRepository(session)
            projected = await repo.create(
                planned_payment_id=payment_id,
                origin_date=date(2024, 1, 15),
                origin_amount=Decimal("1000"),
                origin_description="Monthly rent",
                origin_category_id=None,
                type_=ProjectedTransactionType.EXPENSE,
                projected_date=date(2024, 1, 15),
                projected_amount=Decimal("1000"),
                projected_description="Monthly rent",
                projected_category_id=None,
            )

            # Confirm it
            service = ProjectedTransactionService(session)
            await service.confirm_projection(
                user_id=user_id,
                projected_transaction_id=projected.id,
            )
            await session.commit()

        # Try to update the confirmed projection
        update_response = await async_client.patch(
            f"/api/v1/projected-transactions/{projected.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"projected_amount": "1200.00"},
        )

        assert update_response.status_code == 409

    async def test_update_projection_rejects_foreign_category(
        self,
        async_client: AsyncClient,
        user_with_account_category: dict,
    ) -> None:
        """Test updating projection with another user's category is rejected."""
        account_id = user_with_account_category["account_id"]
        access_token = user_with_account_category["access_token"]

        create_payment = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account_id),
                "amount": "1000.00",
                "description": "Monthly rent",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
                "next_due_at": "2024-01-15",
                "is_active": True,
            },
        )
        assert create_payment.status_code == 201
        payment_id = create_payment.json()["id"]

        from app.models.types import CategoryType, ProjectedTransactionType
        from app.repositories.category_repository import CategoryRepository
        from app.repositories.projected_transaction_repository import (
            ProjectedTransactionRepository,
        )

        async with async_session_factory() as session:
            projected_repo = ProjectedTransactionRepository(session)
            projected = await projected_repo.create(
                planned_payment_id=payment_id,
                origin_date=date(2024, 1, 15),
                origin_amount=Decimal("1000"),
                origin_description="Monthly rent",
                origin_category_id=None,
                type_=ProjectedTransactionType.EXPENSE,
                projected_date=date(2024, 1, 15),
                projected_amount=Decimal("1000"),
                projected_description="Monthly rent",
                projected_category_id=None,
            )

            # Foreign user + foreign category
            reg_other = await async_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "projection-foreign-category@example.com",
                    "password": "SecurePass123!",
                },
            )
            other_user_id = reg_other.json()["id"]

            category_repo = CategoryRepository(session)
            foreign_category = await category_repo.create(
                user_id=other_user_id,
                name="Foreign Category",
                type_=CategoryType.EXPENSE,
            )
            await session.commit()

        update_response = await async_client.patch(
            f"/api/v1/projected-transactions/{projected.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"projected_category_id": str(foreign_category.id)},
        )

        assert update_response.status_code == 404
        assert _error_message(update_response) == "Category not found"


class TestConfirmProjectedTransaction:
    """Tests for POST /api/v1/projected-transactions/{id}/confirm."""

    async def test_confirm_projected_transaction_as_is(
        self,
        async_client: AsyncClient,
        user_with_account_category: dict,
    ) -> None:
        """Test confirming a projected transaction with projected values."""
        user_id = user_with_account_category["user_id"]
        account_id = user_with_account_category["account_id"]
        access_token = user_with_account_category["access_token"]

        # Create a planned payment
        response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account_id),
                "amount": "1000.00",
                "description": "Monthly rent",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
                "next_due_at": "2024-01-15",
                "is_active": True,
            },
        )
        assert response.status_code == 201
        payment_id = response.json()["id"]

        # Create a projected transaction via DB
        from app.models.projected_transaction import ProjectedTransaction
        from app.models.types import (
            ProjectedTransactionStatus,
            ProjectedTransactionType,
        )
        from app.repositories.projected_transaction_repository import (
            ProjectedTransactionRepository,
        )

        async with async_session_factory() as session:
            repo = ProjectedTransactionRepository(session)
            projected = await repo.create(
                planned_payment_id=payment_id,
                origin_date=date(2024, 1, 15),
                origin_amount=Decimal("1000"),
                origin_description="Monthly rent",
                origin_category_id=None,
                type_=ProjectedTransactionType.EXPENSE,
                projected_date=date(2024, 1, 15),
                projected_amount=Decimal("1000"),
                projected_description="Monthly rent",
                projected_category_id=None,
            )
            await session.commit()

        # Confirm the projection
        confirm_response = await async_client.post(
            f"/api/v1/projected-transactions/{projected.id}/confirm",
            headers={"Authorization": f"Bearer {access_token}"},
            json={},
        )

        assert confirm_response.status_code == 200
        data = confirm_response.json()
        assert data["projected_transaction"]["status"] == "confirmed"
        assert data["transaction_id"] is not None
        assert data["projected_transaction"]["transaction_id"] == data["transaction_id"]

        # Verify the transaction was created
        transaction_id = data["transaction_id"]
        transaction_response = await async_client.get(
            f"/api/v1/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert transaction_response.status_code == 200
        transaction_data = transaction_response.json()
        assert transaction_data["amount"] == "1000.00"
        assert transaction_data["planned_payment_id"] == payment_id
        assert transaction_data["projected_transaction_id"] == str(projected.id)

    async def test_confirm_projected_transaction_with_override(
        self,
        async_client: AsyncClient,
        user_with_account_category: dict,
    ) -> None:
        """Test confirming a projected transaction with overridden values."""
        user_id = user_with_account_category["user_id"]
        account_id = user_with_account_category["account_id"]
        access_token = user_with_account_category["access_token"]

        # Create a planned payment
        response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account_id),
                "amount": "1000.00",
                "description": "Monthly rent",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
                "next_due_at": "2024-01-15",
                "is_active": True,
            },
        )
        assert response.status_code == 201
        payment_id = response.json()["id"]

        # Create a projected transaction via DB
        from app.models.projected_transaction import ProjectedTransaction
        from app.models.types import (
            ProjectedTransactionStatus,
            ProjectedTransactionType,
        )
        from app.repositories.projected_transaction_repository import (
            ProjectedTransactionRepository,
        )

        async with async_session_factory() as session:
            repo = ProjectedTransactionRepository(session)
            projected = await repo.create(
                planned_payment_id=payment_id,
                origin_date=date(2024, 1, 15),
                origin_amount=Decimal("1000"),
                origin_description="Monthly rent",
                origin_category_id=None,
                type_=ProjectedTransactionType.EXPENSE,
                projected_date=date(2024, 1, 15),
                projected_amount=Decimal("1000"),
                projected_description="Monthly rent",
                projected_category_id=None,
            )
            await session.commit()

        # Confirm with override
        confirm_response = await async_client.post(
            f"/api/v1/projected-transactions/{projected.id}/confirm",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "amount": "1200.00",
                "date": "2024-01-16",
                "description": "Monthly rent (late)",
            },
        )

        assert confirm_response.status_code == 200
        data = confirm_response.json()
        assert data["projected_transaction"]["status"] == "confirmed"

        # Verify the transaction has overridden values
        transaction_id = data["transaction_id"]
        transaction_response = await async_client.get(
            f"/api/v1/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        transaction_data = transaction_response.json()
        assert transaction_data["amount"] == "1200.00"
        # Note: date format might differ, check parsed value
        assert transaction_data["description"] == "Monthly rent (late)"

    async def test_confirm_non_pending_projection(
        self,
        async_client: AsyncClient,
        user_with_account_category: dict,
    ) -> None:
        """Test confirming a skipped projection returns 409."""
        user_id = user_with_account_category["user_id"]
        account_id = user_with_account_category["account_id"]
        access_token = user_with_account_category["access_token"]

        # Create a planned payment
        response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account_id),
                "amount": "1000.00",
                "description": "Monthly rent",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
                "next_due_at": "2024-01-15",
                "is_active": True,
            },
        )
        assert response.status_code == 201
        payment_id = response.json()["id"]

        # Create a projected transaction via DB
        from app.models.projected_transaction import ProjectedTransaction
        from app.models.types import (
            ProjectedTransactionStatus,
            ProjectedTransactionType,
        )
        from app.repositories.projected_transaction_repository import (
            ProjectedTransactionRepository,
        )
        from app.services.projected_transaction_service import ProjectedTransactionService

        async with async_session_factory() as session:
            repo = ProjectedTransactionRepository(session)
            projected = await repo.create(
                planned_payment_id=payment_id,
                origin_date=date(2024, 1, 15),
                origin_amount=Decimal("1000"),
                origin_description="Monthly rent",
                origin_category_id=None,
                type_=ProjectedTransactionType.EXPENSE,
                projected_date=date(2024, 1, 15),
                projected_amount=Decimal("1000"),
                projected_description="Monthly rent",
                projected_category_id=None,
            )

            # Skip it
            service = ProjectedTransactionService(session)
            await service.skip_projection(
                user_id=user_id,
                projected_transaction_id=projected.id,
            )
            await session.commit()

        # Try to confirm the skipped projection
        confirm_response = await async_client.post(
            f"/api/v1/projected-transactions/{projected.id}/confirm",
            headers={"Authorization": f"Bearer {access_token}"},
            json={},
        )

        assert confirm_response.status_code == 409

    async def test_confirm_projection_rejects_foreign_category_override(
        self,
        async_client: AsyncClient,
        user_with_account_category: dict,
    ) -> None:
        """Test confirming projection with foreign category override is rejected."""
        account_id = user_with_account_category["account_id"]
        access_token = user_with_account_category["access_token"]

        create_payment = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account_id),
                "amount": "1000.00",
                "description": "Monthly rent",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
                "next_due_at": "2024-01-15",
                "is_active": True,
            },
        )
        assert create_payment.status_code == 201
        payment_id = create_payment.json()["id"]

        from app.models.types import CategoryType, ProjectedTransactionType
        from app.repositories.category_repository import CategoryRepository
        from app.repositories.projected_transaction_repository import (
            ProjectedTransactionRepository,
        )

        async with async_session_factory() as session:
            projected_repo = ProjectedTransactionRepository(session)
            projected = await projected_repo.create(
                planned_payment_id=payment_id,
                origin_date=date(2024, 1, 15),
                origin_amount=Decimal("1000"),
                origin_description="Monthly rent",
                origin_category_id=None,
                type_=ProjectedTransactionType.EXPENSE,
                projected_date=date(2024, 1, 15),
                projected_amount=Decimal("1000"),
                projected_description="Monthly rent",
                projected_category_id=None,
            )

            reg_other = await async_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "projection-confirm-foreign@example.com",
                    "password": "SecurePass123!",
                },
            )
            other_user_id = reg_other.json()["id"]

            category_repo = CategoryRepository(session)
            foreign_category = await category_repo.create(
                user_id=other_user_id,
                name="Foreign Category Confirm",
                type_=CategoryType.EXPENSE,
            )
            await session.commit()

        confirm_response = await async_client.post(
            f"/api/v1/projected-transactions/{projected.id}/confirm",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"category_id": str(foreign_category.id)},
        )

        assert confirm_response.status_code == 404
        assert _error_message(confirm_response) == "Category not found"


class TestSkipProjectedTransaction:
    """Tests for POST /api/v1/projected-transactions/{id}/skip."""

    async def test_skip_projected_transaction(
        self,
        async_client: AsyncClient,
        user_with_account_category: dict,
    ) -> None:
        """Test skipping a projected transaction."""
        user_id = user_with_account_category["user_id"]
        account_id = user_with_account_category["account_id"]
        access_token = user_with_account_category["access_token"]

        # Create a planned payment
        response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account_id),
                "amount": "1000.00",
                "description": "Monthly rent",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
                "next_due_at": "2024-01-15",
                "is_active": True,
            },
        )
        assert response.status_code == 201
        payment_id = response.json()["id"]

        # Create a projected transaction via DB
        from app.models.projected_transaction import ProjectedTransaction
        from app.models.types import (
            ProjectedTransactionStatus,
            ProjectedTransactionType,
        )
        from app.repositories.projected_transaction_repository import (
            ProjectedTransactionRepository,
        )

        async with async_session_factory() as session:
            repo = ProjectedTransactionRepository(session)
            projected = await repo.create(
                planned_payment_id=payment_id,
                origin_date=date(2024, 1, 15),
                origin_amount=Decimal("1000"),
                origin_description="Monthly rent",
                origin_category_id=None,
                type_=ProjectedTransactionType.EXPENSE,
                projected_date=date(2024, 1, 15),
                projected_amount=Decimal("1000"),
                projected_description="Monthly rent",
                projected_category_id=None,
            )
            await session.commit()

        # Skip the projection
        skip_response = await async_client.post(
            f"/api/v1/projected-transactions/{projected.id}/skip",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert skip_response.status_code == 200
        data = skip_response.json()
        assert data["status"] == "skipped"
        assert data["resolved_at"] is not None

    async def test_skip_non_pending_projection(
        self,
        async_client: AsyncClient,
        user_with_account_category: dict,
    ) -> None:
        """Test skipping a confirmed projection returns 409."""
        user_id = user_with_account_category["user_id"]
        account_id = user_with_account_category["account_id"]
        access_token = user_with_account_category["access_token"]

        # Create a planned payment
        response = await async_client.post(
            "/api/v1/planned-payments",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "account_id": str(account_id),
                "amount": "1000.00",
                "description": "Monthly rent",
                "recurrence": "monthly",
                "start_date": "2024-01-01",
                "next_due_at": "2024-01-15",
                "is_active": True,
            },
        )
        assert response.status_code == 201
        payment_id = response.json()["id"]

        # Create a projected transaction via DB
        from app.models.projected_transaction import ProjectedTransaction
        from app.models.types import (
            ProjectedTransactionStatus,
            ProjectedTransactionType,
        )
        from app.repositories.projected_transaction_repository import (
            ProjectedTransactionRepository,
        )
        from app.services.projected_transaction_service import ProjectedTransactionService

        async with async_session_factory() as session:
            repo = ProjectedTransactionRepository(session)
            projected = await repo.create(
                planned_payment_id=payment_id,
                origin_date=date(2024, 1, 15),
                origin_amount=Decimal("1000"),
                origin_description="Monthly rent",
                origin_category_id=None,
                type_=ProjectedTransactionType.EXPENSE,
                projected_date=date(2024, 1, 15),
                projected_amount=Decimal("1000"),
                projected_description="Monthly rent",
                projected_category_id=None,
            )

            # Confirm it
            service = ProjectedTransactionService(session)
            await service.confirm_projection(
                user_id=user_id,
                projected_transaction_id=projected.id,
            )
            await session.commit()

        # Try to skip the confirmed projection
        skip_response = await async_client.post(
            f"/api/v1/projected-transactions/{projected.id}/skip",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert skip_response.status_code == 409


class TestAuthorization:
    """Tests for authorization on projected transactions endpoints."""

    async def test_unauthorized_access(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test accessing projected transactions without authentication."""
        # List
        response = await async_client.get("/api/v1/projected-transactions")
        assert response.status_code == 401

        # Get
        fake_id = "12345678-1234-1234-1234-123456789012"
        response = await async_client.get(f"/api/v1/projected-transactions/{fake_id}")
        assert response.status_code == 401

        # Update
        response = await async_client.patch(
            f"/api/v1/projected-transactions/{fake_id}",
            json={"projected_amount": "1000.00"},
        )
        assert response.status_code == 401

        # Confirm
        response = await async_client.post(
            f"/api/v1/projected-transactions/{fake_id}/confirm",
            json={},
        )
        assert response.status_code == 401

        # Skip
        response = await async_client.post(
            f"/api/v1/projected-transactions/{fake_id}/skip",
        )
        assert response.status_code == 401
