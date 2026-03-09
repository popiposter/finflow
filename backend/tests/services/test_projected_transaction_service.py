"""Service tests for projected transaction service."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.models.projected_transaction import ProjectedTransaction
from app.models.types import (
    AccountType,
    CategoryType,
    ProjectedTransactionStatus,
    ProjectedTransactionType,
)
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.planned_payment_repository import PlannedPaymentRepository
from app.repositories.projected_transaction_repository import ProjectedTransactionRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.projected_transaction_service import ProjectedTransactionService
from app.services.planned_payment_service import PlannedPaymentGenerationService


class TestProjectedTransactionService:
    """Tests for ProjectedTransactionService."""

    async def test_update_projection(
        self,
        db_session,
        test_account_with_user: tuple,
    ) -> None:
        """Test updating a pending projected transaction."""
        user_id, account = test_account_with_user

        # Create a planned payment
        planned_payment_repo = PlannedPaymentRepository(db_session)
        planned_payment = await planned_payment_repo.create(
            user_id=user_id,
            account_id=account.id,
            amount=Decimal("1000.00"),
            recurrence="monthly",
            start_date=date(2024, 1, 1),
            next_due_at=date(2024, 1, 15),
            description="Monthly rent",
        )

        # Create a projected transaction
        projected_repo = ProjectedTransactionRepository(db_session)
        projected = await projected_repo.create(
            planned_payment_id=planned_payment.id,
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

        # Update the projection
        service = ProjectedTransactionService(db_session)
        updated = await service.update_projection(
            user_id=user_id,
            projected_transaction_id=projected.id,
            projected_amount=Decimal("1200.00"),
            projected_description="Monthly rent with increase",
        )

        assert updated.projected_amount == Decimal("1200.00")
        assert updated.projected_description == "Monthly rent with increase"
        assert updated.origin_amount == Decimal("1000.00")  # Origin should not change
        assert updated.status == ProjectedTransactionStatus.PENDING
        assert updated.version == 2

    async def test_update_non_pending_projection_raises(
        self,
        db_session,
        test_account_with_user: tuple,
    ) -> None:
        """Test updating a confirmed projection raises error."""
        user_id, account = test_account_with_user

        # Create a planned payment
        planned_payment_repo = PlannedPaymentRepository(db_session)
        planned_payment = await planned_payment_repo.create(
            user_id=user_id,
            account_id=account.id,
            amount=Decimal("1000.00"),
            recurrence="monthly",
            start_date=date(2024, 1, 1),
            next_due_at=date(2024, 1, 15),
            description="Monthly rent",
        )

        # Create a projected transaction
        projected_repo = ProjectedTransactionRepository(db_session)
        projected = await projected_repo.create(
            planned_payment_id=planned_payment.id,
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
        service = ProjectedTransactionService(db_session)
        _, transaction_id = await service.confirm_projection(
            user_id=user_id,
            projected_transaction_id=projected.id,
        )

        # Try to update the confirmed projection
        with pytest.raises(RuntimeError, match="Cannot update projection"):
            await service.update_projection(
                user_id=user_id,
                projected_transaction_id=projected.id,
                projected_amount=Decimal("1200.00"),
            )

    async def test_confirm_projection(
        self,
        db_session,
        test_account_with_user: tuple,
    ) -> None:
        """Test confirming a projected transaction."""
        user_id, account = test_account_with_user

        # Create a planned payment
        planned_payment_repo = PlannedPaymentRepository(db_session)
        planned_payment = await planned_payment_repo.create(
            user_id=user_id,
            account_id=account.id,
            amount=Decimal("1000.00"),
            recurrence="monthly",
            start_date=date(2024, 1, 1),
            next_due_at=date(2024, 1, 15),
            description="Monthly rent",
        )

        # Create a projected transaction
        projected_repo = ProjectedTransactionRepository(db_session)
        projected = await projected_repo.create(
            planned_payment_id=planned_payment.id,
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

        # Confirm the projection
        service = ProjectedTransactionService(db_session)
        updated, transaction_id = await service.confirm_projection(
            user_id=user_id,
            projected_transaction_id=projected.id,
        )

        assert updated.status == ProjectedTransactionStatus.CONFIRMED
        assert updated.transaction_id == transaction_id
        assert updated.version == 2
        assert updated.resolved_at is not None

        # Verify the transaction was created
        transaction_repo = TransactionRepository(db_session)
        transaction = await transaction_repo.get_by_id(transaction_id)
        assert transaction is not None
        assert transaction.amount == Decimal("1000.00")
        assert transaction.planned_payment_id == planned_payment.id
        assert transaction.projected_transaction_id == projected.id

    async def test_confirm_projection_with_override(
        self,
        db_session,
        test_account_with_user: tuple,
    ) -> None:
        """Test confirming a projected transaction with overridden values."""
        user_id, account = test_account_with_user

        # Create a planned payment
        planned_payment_repo = PlannedPaymentRepository(db_session)
        planned_payment = await planned_payment_repo.create(
            user_id=user_id,
            account_id=account.id,
            amount=Decimal("1000.00"),
            recurrence="monthly",
            start_date=date(2024, 1, 1),
            next_due_at=date(2024, 1, 15),
            description="Monthly rent",
        )

        # Create a projected transaction
        projected_repo = ProjectedTransactionRepository(db_session)
        projected = await projected_repo.create(
            planned_payment_id=planned_payment.id,
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

        # Confirm with override
        service = ProjectedTransactionService(db_session)
        updated, transaction_id = await service.confirm_projection(
            user_id=user_id,
            projected_transaction_id=projected.id,
            amount=Decimal("1200.00"),
            date_=datetime(2024, 1, 16),
            description="Monthly rent (late)",
        )

        assert updated.status == ProjectedTransactionStatus.CONFIRMED

        # Verify the transaction has overridden values
        transaction_repo = TransactionRepository(db_session)
        transaction = await transaction_repo.get_by_id(transaction_id)
        assert transaction is not None
        assert transaction.amount == Decimal("1200.00")
        assert transaction.date_accrual.date() == date(2024, 1, 16)
        assert transaction.description == "Monthly rent (late)"

    async def test_skip_projection(
        self,
        db_session,
        test_account_with_user: tuple,
    ) -> None:
        """Test skipping a projected transaction."""
        user_id, account = test_account_with_user

        # Create a planned payment
        planned_payment_repo = PlannedPaymentRepository(db_session)
        planned_payment = await planned_payment_repo.create(
            user_id=user_id,
            account_id=account.id,
            amount=Decimal("1000.00"),
            recurrence="monthly",
            start_date=date(2024, 1, 1),
            next_due_at=date(2024, 1, 15),
            description="Monthly rent",
        )

        # Create a projected transaction
        projected_repo = ProjectedTransactionRepository(db_session)
        projected = await projected_repo.create(
            planned_payment_id=planned_payment.id,
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

        # Skip the projection
        service = ProjectedTransactionService(db_session)
        updated = await service.skip_projection(
            user_id=user_id,
            projected_transaction_id=projected.id,
        )

        assert updated.status == ProjectedTransactionStatus.SKIPPED
        assert updated.version == 2
        assert updated.resolved_at is not None

        # Verify no transaction was created
        transaction_repo = TransactionRepository(db_session)
        transactions = await transaction_repo.get_by_user(user_id)
        # Only transactions from planned_payments should exist
        assert len(transactions) == 0

    async def test_skip_non_pending_projection_raises(
        self,
        db_session,
        test_account_with_user: tuple,
    ) -> None:
        """Test skipping a confirmed projection raises error."""
        user_id, account = test_account_with_user

        # Create a planned payment
        planned_payment_repo = PlannedPaymentRepository(db_session)
        planned_payment = await planned_payment_repo.create(
            user_id=user_id,
            account_id=account.id,
            amount=Decimal("1000.00"),
            recurrence="monthly",
            start_date=date(2024, 1, 1),
            next_due_at=date(2024, 1, 15),
            description="Monthly rent",
        )

        # Create a projected transaction
        projected_repo = ProjectedTransactionRepository(db_session)
        projected = await projected_repo.create(
            planned_payment_id=planned_payment.id,
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
        service = ProjectedTransactionService(db_session)
        await service.confirm_projection(
            user_id=user_id,
            projected_transaction_id=projected.id,
        )

        # Try to skip the confirmed projection
        with pytest.raises(RuntimeError, match="Cannot skip projection"):
            await service.skip_projection(
                user_id=user_id,
                projected_transaction_id=projected.id,
            )

    async def test_confirm_projection_atomicity(
        self,
        db_session,
        test_account_with_user: tuple,
    ) -> None:
        """Test that confirm_projection is atomic (version check)."""
        user_id, account = test_account_with_user

        # Create a planned payment
        planned_payment_repo = PlannedPaymentRepository(db_session)
        planned_payment = await planned_payment_repo.create(
            user_id=user_id,
            account_id=account.id,
            amount=Decimal("1000.00"),
            recurrence="monthly",
            start_date=date(2024, 1, 1),
            next_due_at=date(2024, 1, 15),
            description="Monthly rent",
        )

        # Create a projected transaction
        projected_repo = ProjectedTransactionRepository(db_session)
        projected = await projected_repo.create(
            planned_payment_id=planned_payment.id,
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

        # First confirm
        service = ProjectedTransactionService(db_session)
        updated1, transaction_id1 = await service.confirm_projection(
            user_id=user_id,
            projected_transaction_id=projected.id,
        )

        # Version should be 2 after first confirmation
        assert updated1.version == 2

        # Second attempt should fail because status is now CONFIRMED
        with pytest.raises(RuntimeError, match="Cannot confirm projection"):
            await service.confirm_projection(
                user_id=user_id,
                projected_transaction_id=projected.id,
            )

        # Should only have one transaction
        transaction_repo = TransactionRepository(db_session)
        transactions = await transaction_repo.get_by_user(user_id)
        assert len(transactions) == 1

    async def test_list_projections(
        self,
        db_session,
        test_account_with_user: tuple,
    ) -> None:
        """Test listing projected transactions."""
        user_id, account = test_account_with_user

        # Create a planned payment
        planned_payment_repo = PlannedPaymentRepository(db_session)
        planned_payment = await planned_payment_repo.create(
            user_id=user_id,
            account_id=account.id,
            amount=Decimal("1000.00"),
            recurrence="monthly",
            start_date=date(2024, 1, 1),
            next_due_at=date(2024, 1, 15),
            description="Monthly rent",
        )

        # Create projected transactions
        projected_repo = ProjectedTransactionRepository(db_session)
        projected1 = await projected_repo.create(
            planned_payment_id=planned_payment.id,
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
        projected2 = await projected_repo.create(
            planned_payment_id=planned_payment.id,
            origin_date=date(2024, 2, 15),
            origin_amount=Decimal("1000"),
            origin_description="Monthly rent",
            origin_category_id=None,
            type_=ProjectedTransactionType.EXPENSE,
            projected_date=date(2024, 2, 15),
            projected_amount=Decimal("1000"),
            projected_description="Monthly rent",
            projected_category_id=None,
        )

        # List all
        service = ProjectedTransactionService(db_session)
        all_projections = await service.list_projections(user_id=user_id)
        assert len(all_projections) == 2

        # Filter by status
        pending_projections = await service.list_projections(
            user_id=user_id,
            status=ProjectedTransactionStatus.PENDING,
        )
        assert len(pending_projections) == 2

        # Filter by date range
        projections = await service.list_projections(
            user_id=user_id,
            from_date=date(2024, 1, 1),
            to_date=date(2024, 1, 31),
        )
        assert len(projections) == 1
        assert projections[0].origin_date == date(2024, 1, 15)

    async def test_get_projection(
        self,
        db_session,
        test_account_with_user: tuple,
    ) -> None:
        """Test getting a specific projected transaction."""
        user_id, account = test_account_with_user

        # Create a planned payment
        planned_payment_repo = PlannedPaymentRepository(db_session)
        planned_payment = await planned_payment_repo.create(
            user_id=user_id,
            account_id=account.id,
            amount=Decimal("1000.00"),
            recurrence="monthly",
            start_date=date(2024, 1, 1),
            next_due_at=date(2024, 1, 15),
            description="Monthly rent",
        )

        # Create a projected transaction
        projected_repo = ProjectedTransactionRepository(db_session)
        projected = await projected_repo.create(
            planned_payment_id=planned_payment.id,
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

        # Get the projection
        service = ProjectedTransactionService(db_session)
        retrieved = await service.get_projection(
            user_id=user_id,
            projected_transaction_id=projected.id,
        )

        assert retrieved is not None
        assert retrieved.id == projected.id

    async def test_get_projection_not_found(
        self,
        db_session,
        test_account_with_user: tuple,
    ) -> None:
        """Test getting a non-existent projected transaction returns None."""
        user_id, account = test_account_with_user

        fake_id = uuid4()
        service = ProjectedTransactionService(db_session)
        retrieved = await service.get_projection(
            user_id=user_id,
            projected_transaction_id=fake_id,
        )

        assert retrieved is None

    async def test_origin_snapshot_preserved(
        self,
        db_session,
        test_account_with_user: tuple,
    ) -> None:
        """Test that origin_* fields are preserved and never updated."""
        user_id, account = test_account_with_user

        # Create a planned payment
        planned_payment_repo = PlannedPaymentRepository(db_session)
        planned_payment = await planned_payment_repo.create(
            user_id=user_id,
            account_id=account.id,
            amount=Decimal("1000.00"),
            recurrence="monthly",
            start_date=date(2024, 1, 1),
            next_due_at=date(2024, 1, 15),
            description="Original description",
        )

        # Create a projected transaction
        projected_repo = ProjectedTransactionRepository(db_session)
        projected = await projected_repo.create(
            planned_payment_id=planned_payment.id,
            origin_date=date(2024, 1, 15),
            origin_amount=Decimal("1000"),
            origin_description="Original description",
            origin_category_id=None,
            type_=ProjectedTransactionType.EXPENSE,
            projected_date=date(2024, 1, 15),
            projected_amount=Decimal("1000"),
            projected_description="Original description",
            projected_category_id=None,
        )

        # Update the projected values
        service = ProjectedTransactionService(db_session)
        updated = await service.update_projection(
            user_id=user_id,
            projected_transaction_id=projected.id,
            projected_amount=Decimal("1500.00"),
            projected_description="Updated description",
        )

        # Origin should remain unchanged
        assert updated.origin_amount == Decimal("1000.00")
        assert updated.origin_description == "Original description"
        assert updated.origin_date == date(2024, 1, 15)

        # Projected should be updated
        assert updated.projected_amount == Decimal("1500.00")
        assert updated.projected_description == "Updated description"
