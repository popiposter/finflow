"""Service tests for transaction editing."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.exceptions import TransactionNotFoundError
from app.models.account import Account
from app.models.category import Category
from app.models.planned_payment import PlannedPayment
from app.models.projected_transaction import ProjectedTransaction
from app.models.transaction import Transaction
from app.models.types import (
    AccountType,
    CategoryType,
    ProjectedTransactionStatus,
    ProjectedTransactionType,
    Recurrence,
    TransactionType,
)
from app.models.user import User
from app.services.transaction_service import TransactionService

pytestmark = pytest.mark.integration


async def _build_transaction_fixture(db_session):
    """Create a linked projected/actual transaction fixture."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email=f"{user_id}@example.com",
        hashed_password="hash",
        is_active=True,
    )
    account = Account(
        user_id=user_id,
        name="Main account",
        type=AccountType.CHECKING,
        currency_code="USD",
        current_balance=Decimal("0.00"),
    )
    category = Category(
        user_id=user_id,
        name="Salary",
        type=CategoryType.INCOME,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add_all([account, category])
    await db_session.flush()

    planned_payment = PlannedPayment(
        user_id=user_id,
        account_id=account.id,
        category_id=category.id,
        amount=Decimal("100.00"),
        description="Projected salary",
        recurrence=Recurrence.MONTHLY,
        start_date=date(2024, 1, 15),
        next_due_at=date(2024, 1, 15),
        is_active=True,
    )
    db_session.add(planned_payment)
    await db_session.flush()

    actual_transaction = Transaction(
        user_id=user_id,
        account_id=account.id,
        category_id=category.id,
        amount=Decimal("100.00"),
        type=TransactionType.INCOME,
        description="Salary fact",
        date_accrual=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
        date_cash=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
        planned_payment_id=planned_payment.id,
    )
    db_session.add(actual_transaction)
    await db_session.flush()

    projection = ProjectedTransaction(
        planned_payment_id=planned_payment.id,
        origin_date=date(2024, 1, 15),
        origin_amount=Decimal("100.00"),
        origin_description="Projected salary",
        origin_category_id=category.id,
        type=ProjectedTransactionType.INCOME,
        projected_date=date(2024, 1, 15),
        projected_amount=Decimal("100.00"),
        projected_description="Projected salary",
        projected_category_id=category.id,
        status=ProjectedTransactionStatus.CONFIRMED,
        transaction_id=actual_transaction.id,
    )
    db_session.add(projection)
    await db_session.flush()

    actual_transaction.projected_transaction_id = projection.id
    await db_session.commit()

    return {
        "user_id": user_id,
        "account_id": account.id,
        "category_id": category.id,
        "planned_payment_id": planned_payment.id,
        "transaction_id": actual_transaction.id,
        "projection_id": projection.id,
    }


class TestTransactionService:
    """Tests for transaction update service."""

    async def test_update_transaction_does_not_modify_linked_projection(
        self, db_session
    ) -> None:
        """Updating an actual transaction should not rewrite the projection."""
        fixture = await _build_transaction_fixture(db_session)
        service = TransactionService(db_session)

        updated = await service.update_transaction(
            transaction_id=fixture["transaction_id"],
            user_id=fixture["user_id"],
            amount=Decimal("148.00"),
            description="Salary (fact)",
            date_cash=datetime(2024, 1, 16, 10, 0, tzinfo=UTC),
        )

        projection = await db_session.get(
            ProjectedTransaction,
            fixture["projection_id"],
        )

        assert updated.amount == Decimal("148.00")
        assert updated.description == "Salary (fact)"
        assert updated.projected_transaction_id == fixture["projection_id"]
        assert projection is not None
        assert projection.projected_amount == Decimal("100.00")
        assert projection.projected_description == "Projected salary"
        assert projection.projected_date == date(2024, 1, 15)

    async def test_update_transaction_requires_ownership(self, db_session) -> None:
        """Service should raise not found for another user's transaction."""
        fixture = await _build_transaction_fixture(db_session)
        service = TransactionService(db_session)

        with pytest.raises(TransactionNotFoundError):
            await service.update_transaction(
                transaction_id=fixture["transaction_id"],
                user_id=uuid4(),
                amount=Decimal("120.00"),
            )
