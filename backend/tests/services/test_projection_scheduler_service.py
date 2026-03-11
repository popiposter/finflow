"""Service tests for projection scheduler generation."""

from datetime import date
from decimal import Decimal

import pytest

from app.models.types import CategoryType, ProjectedTransactionType, Recurrence
from app.repositories.category_repository import CategoryRepository
from app.repositories.planned_payment_repository import PlannedPaymentRepository
from app.repositories.projected_transaction_repository import (
    ProjectedTransactionRepository,
)
from app.repositories.transaction_repository import TransactionRepository
from app.services.projection_scheduler_service import ProjectionSchedulerService


pytestmark = pytest.mark.integration


class TestProjectionSchedulerService:
    """Tests for scheduler-facing projection generation."""

    async def test_generate_due_projection_creates_projection_not_transaction(
        self,
        db_session,
        test_account_with_user: tuple,
    ) -> None:
        """A due payment should create one pending projected transaction."""
        user_id, account = test_account_with_user
        planned_payment_repo = PlannedPaymentRepository(db_session)

        payment = await planned_payment_repo.create(
            user_id=user_id,
            account_id=account.id,
            amount=Decimal("1000.00"),
            recurrence=Recurrence.MONTHLY,
            start_date=date(2024, 1, 15),
            next_due_at=date(2024, 1, 15),
            description="Monthly rent",
        )

        service = ProjectionSchedulerService(db_session)
        results = await service.generate_due_projections(
            user_id=user_id,
            as_of_date=date(2024, 1, 15),
        )

        assert len(results) == 1
        assert len(results[0].generated_projections) == 1
        assert results[0].skipped_occurrences == 0

        projection_repo = ProjectedTransactionRepository(db_session)
        transaction_repo = TransactionRepository(db_session)
        projections = await projection_repo.get_by_planned_payment(payment.id)
        transactions = await transaction_repo.get_by_user(user_id)

        assert len(projections) == 1
        assert projections[0].status.value == "pending"
        assert projections[0].type == ProjectedTransactionType.EXPENSE
        assert len(transactions) == 0

        updated_payment = await planned_payment_repo.get_by_id(payment.id)
        assert updated_payment is not None
        assert updated_payment.next_due_at == date(2024, 2, 15)

    async def test_generate_due_projection_uses_income_category_type(
        self,
        db_session,
        test_account_with_user: tuple,
    ) -> None:
        """Income categories should map planned payments to income projections."""
        user_id, account = test_account_with_user
        category_repo = CategoryRepository(db_session)
        income_category = await category_repo.create(
            user_id=user_id,
            name="Salary",
            type_=CategoryType.INCOME,
        )

        planned_payment_repo = PlannedPaymentRepository(db_session)
        payment = await planned_payment_repo.create(
            user_id=user_id,
            account_id=account.id,
            amount=Decimal("3000.00"),
            recurrence=Recurrence.MONTHLY,
            start_date=date(2024, 1, 1),
            next_due_at=date(2024, 1, 1),
            category_id=income_category.id,
            description="Salary",
        )

        service = ProjectionSchedulerService(db_session)
        await service.generate_due_projections(
            user_id=user_id,
            as_of_date=date(2024, 1, 1),
        )

        projection_repo = ProjectedTransactionRepository(db_session)
        projections = await projection_repo.get_by_planned_payment(payment.id)
        assert len(projections) == 1
        assert projections[0].type == ProjectedTransactionType.INCOME

    async def test_generate_due_projection_is_idempotent_on_repeat(
        self,
        db_session,
        test_account_with_user: tuple,
    ) -> None:
        """Running generation twice for the same date should not duplicate rows."""
        user_id, account = test_account_with_user
        planned_payment_repo = PlannedPaymentRepository(db_session)
        payment = await planned_payment_repo.create(
            user_id=user_id,
            account_id=account.id,
            amount=Decimal("200.00"),
            recurrence=Recurrence.MONTHLY,
            start_date=date(2024, 1, 5),
            next_due_at=date(2024, 1, 5),
            description="Subscription",
        )

        service = ProjectionSchedulerService(db_session)
        first_results = await service.generate_due_projections(
            user_id=user_id,
            as_of_date=date(2024, 1, 5),
        )
        second_results = await service.generate_due_projections(
            user_id=user_id,
            as_of_date=date(2024, 1, 5),
        )

        assert len(first_results) == 1
        assert len(first_results[0].generated_projections) == 1
        assert second_results == []

        projection_repo = ProjectedTransactionRepository(db_session)
        projections = await projection_repo.get_by_planned_payment(payment.id)
        assert len(projections) == 1

    async def test_generate_due_projection_ignores_inactive_and_ended_payments(
        self,
        db_session,
        test_account_with_user: tuple,
    ) -> None:
        """Inactive plans and plans past end_date should not be processed."""
        user_id, account = test_account_with_user
        planned_payment_repo = PlannedPaymentRepository(db_session)

        inactive_payment = await planned_payment_repo.create(
            user_id=user_id,
            account_id=account.id,
            amount=Decimal("100.00"),
            recurrence=Recurrence.MONTHLY,
            start_date=date(2024, 1, 1),
            next_due_at=date(2024, 1, 1),
            is_active=False,
        )
        ended_payment = await planned_payment_repo.create(
            user_id=user_id,
            account_id=account.id,
            amount=Decimal("100.00"),
            recurrence=Recurrence.MONTHLY,
            start_date=date(2024, 1, 1),
            next_due_at=date(2024, 3, 1),
            end_date=date(2024, 2, 1),
        )

        service = ProjectionSchedulerService(db_session)
        results = await service.generate_due_projections(
            user_id=user_id,
            as_of_date=date(2024, 3, 1),
        )

        projection_repo = ProjectedTransactionRepository(db_session)
        inactive_projections = await projection_repo.get_by_planned_payment(
            inactive_payment.id
        )
        ended_projections = await projection_repo.get_by_planned_payment(
            ended_payment.id
        )

        assert results == []
        assert inactive_projections == []
        assert ended_projections == []
