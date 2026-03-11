"""Service tests for unified cashflow ledger."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

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
from app.schemas.finance import CashflowLedgerMode
from app.services.cashflow_service import CashflowService

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def cashflow_fixture_data(db_session):
    """Create a user, account, category, transactions, and projections."""
    opening_date = date.today() - timedelta(days=10)
    report_start = date.today() + timedelta(days=2)
    skipped_date = date.today() + timedelta(days=3)
    confirmed_date = date.today() + timedelta(days=4)
    future_date = date.today() + timedelta(days=5)

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
    expense_category = Category(
        user_id=user_id,
        name="Housing",
        type=CategoryType.EXPENSE,
    )
    income_category = Category(
        user_id=user_id,
        name="Salary",
        type=CategoryType.INCOME,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add_all([account, expense_category, income_category])
    await db_session.flush()

    opening_income = Transaction(
        user_id=user_id,
        account_id=account.id,
        category_id=income_category.id,
        amount=Decimal("1000.00"),
        type=TransactionType.INCOME,
        description="Salary",
        date_accrual=datetime.combine(opening_date, datetime.min.time(), tzinfo=UTC),
        date_cash=datetime.combine(opening_date, datetime.min.time(), tzinfo=UTC),
    )
    in_range_expense = Transaction(
        user_id=user_id,
        account_id=account.id,
        category_id=expense_category.id,
        amount=Decimal("200.00"),
        type=TransactionType.EXPENSE,
        description="Rent",
        date_accrual=datetime.combine(report_start, datetime.min.time(), tzinfo=UTC),
        date_cash=datetime.combine(report_start, datetime.min.time(), tzinfo=UTC),
    )
    confirmed_actual = Transaction(
        user_id=user_id,
        account_id=account.id,
        category_id=expense_category.id,
        amount=Decimal("75.00"),
        type=TransactionType.EXPENSE,
        description="Confirmed bill",
        date_accrual=datetime.combine(confirmed_date, datetime.min.time(), tzinfo=UTC),
        date_cash=datetime.combine(confirmed_date, datetime.min.time(), tzinfo=UTC),
    )
    db_session.add_all([opening_income, in_range_expense, confirmed_actual])
    await db_session.flush()

    pending_payment = PlannedPayment(
        user_id=user_id,
        account_id=account.id,
        category_id=expense_category.id,
        amount=Decimal("300.00"),
        description="Upcoming rent",
        recurrence=Recurrence.MONTHLY,
        start_date=report_start,
        next_due_at=report_start,
        is_active=True,
    )
    skipped_payment = PlannedPayment(
        user_id=user_id,
        account_id=account.id,
        category_id=expense_category.id,
        amount=Decimal("50.00"),
        description="Skipped fee",
        recurrence=Recurrence.MONTHLY,
        start_date=skipped_date,
        next_due_at=skipped_date,
        is_active=True,
    )
    confirmed_payment = PlannedPayment(
        user_id=user_id,
        account_id=account.id,
        category_id=expense_category.id,
        amount=Decimal("75.00"),
        description="Confirmed bill",
        recurrence=Recurrence.MONTHLY,
        start_date=confirmed_date,
        next_due_at=confirmed_date,
        is_active=True,
    )
    income_payment = PlannedPayment(
        user_id=user_id,
        account_id=account.id,
        category_id=income_category.id,
        amount=Decimal("500.00"),
        description="Bonus",
        recurrence=Recurrence.MONTHLY,
        start_date=report_start,
        next_due_at=report_start,
        is_active=True,
    )
    forecast_skipped_payment = PlannedPayment(
        user_id=user_id,
        account_id=account.id,
        category_id=expense_category.id,
        amount=Decimal("40.00"),
        description="Skip me",
        recurrence=Recurrence.MONTHLY,
        start_date=future_date,
        next_due_at=future_date,
        is_active=True,
    )
    db_session.add_all(
        [
            pending_payment,
            skipped_payment,
            confirmed_payment,
            income_payment,
            forecast_skipped_payment,
        ]
    )
    await db_session.flush()

    pending_projection = ProjectedTransaction(
        planned_payment_id=pending_payment.id,
        origin_date=report_start,
        origin_amount=Decimal("300.00"),
        origin_description="Upcoming rent",
        origin_category_id=expense_category.id,
        type=ProjectedTransactionType.EXPENSE,
        projected_date=report_start,
        projected_amount=Decimal("300.00"),
        projected_description="Upcoming rent",
        projected_category_id=expense_category.id,
        status=ProjectedTransactionStatus.PENDING,
    )
    skipped_projection = ProjectedTransaction(
        planned_payment_id=skipped_payment.id,
        origin_date=skipped_date,
        origin_amount=Decimal("50.00"),
        origin_description="Skipped fee",
        origin_category_id=expense_category.id,
        type=ProjectedTransactionType.EXPENSE,
        projected_date=skipped_date,
        projected_amount=Decimal("50.00"),
        projected_description="Skipped fee",
        projected_category_id=expense_category.id,
        status=ProjectedTransactionStatus.SKIPPED,
    )
    confirmed_projection = ProjectedTransaction(
        planned_payment_id=confirmed_payment.id,
        origin_date=confirmed_date,
        origin_amount=Decimal("75.00"),
        origin_description="Confirmed bill",
        origin_category_id=expense_category.id,
        type=ProjectedTransactionType.EXPENSE,
        projected_date=confirmed_date,
        projected_amount=Decimal("75.00"),
        projected_description="Confirmed bill",
        projected_category_id=expense_category.id,
        status=ProjectedTransactionStatus.CONFIRMED,
        transaction_id=confirmed_actual.id,
        resolved_at=datetime.combine(confirmed_date, datetime.min.time(), tzinfo=UTC),
    )
    income_projection = ProjectedTransaction(
        planned_payment_id=income_payment.id,
        origin_date=report_start,
        origin_amount=Decimal("500.00"),
        origin_description="Bonus",
        origin_category_id=income_category.id,
        type=ProjectedTransactionType.INCOME,
        projected_date=report_start,
        projected_amount=Decimal("500.00"),
        projected_description="Bonus",
        projected_category_id=income_category.id,
        status=ProjectedTransactionStatus.PENDING,
    )
    forecast_skipped = ProjectedTransaction(
        planned_payment_id=forecast_skipped_payment.id,
        origin_date=future_date,
        origin_amount=Decimal("40.00"),
        origin_description="Skip me",
        origin_category_id=expense_category.id,
        type=ProjectedTransactionType.EXPENSE,
        projected_date=future_date,
        projected_amount=Decimal("40.00"),
        projected_description="Skip me",
        projected_category_id=expense_category.id,
        status=ProjectedTransactionStatus.SKIPPED,
    )
    db_session.add_all(
        [
            pending_projection,
            skipped_projection,
            confirmed_projection,
            income_projection,
            forecast_skipped,
        ]
    )
    await db_session.commit()

    return {
        "user_id": user_id,
        "report_start": report_start,
        "confirmed_date": confirmed_date,
        "future_date": future_date,
        "opening_income": opening_income,
        "in_range_expense": in_range_expense,
        "confirmed_actual": confirmed_actual,
    }


class TestCashflowService:
    """Tests for the unified cashflow read-model service."""

    async def test_build_report_mixed_mode_running_balance_and_sort(
        self,
        db_session,
        cashflow_fixture_data,
    ) -> None:
        """Mixed mode should include actual rows and pending projections only."""
        service = CashflowService(db_session)

        result = await service.build_report(
            user_id=cashflow_fixture_data["user_id"],
            from_date=cashflow_fixture_data["report_start"],
            to_date=cashflow_fixture_data["confirmed_date"],
        )

        assert result.opening_balance == Decimal("1000.00")
        assert [row.row_type for row in result.rows] == [
            "projected",
            "actual",
            "projected",
            "actual",
        ]
        assert [row.amount for row in result.rows] == [
            Decimal("500.00"),
            Decimal("-200.00"),
            Decimal("-300.00"),
            Decimal("-75.00"),
        ]
        assert result.rows[0].balance_after == Decimal("1500.00")
        assert result.rows[-1].balance_after == Decimal("925.00")
        assert result.closing_balance == Decimal("925.00")

    async def test_build_report_modes_and_skipped_rows(
        self,
        db_session,
        cashflow_fixture_data,
    ) -> None:
        """Mode flags should include the expected subsets of rows."""
        service = CashflowService(db_session)

        actual_only = await service.build_report(
            user_id=cashflow_fixture_data["user_id"],
            from_date=cashflow_fixture_data["report_start"],
            to_date=cashflow_fixture_data["confirmed_date"],
            mode=CashflowLedgerMode.ACTUAL_ONLY,
        )
        planned_only = await service.build_report(
            user_id=cashflow_fixture_data["user_id"],
            from_date=cashflow_fixture_data["report_start"],
            to_date=cashflow_fixture_data["confirmed_date"],
            mode=CashflowLedgerMode.PLANNED_ONLY,
            include_skipped=True,
        )

        assert [row.row_type for row in actual_only.rows] == ["actual", "actual"]
        assert [row.row_type for row in planned_only.rows] == [
            "projected",
            "projected",
            "projected",
        ]
        assert {row.status for row in planned_only.rows} == {"pending", "skipped"}

    async def test_forecast_summary_excludes_skipped_and_confirmed(
        self,
        db_session,
        cashflow_fixture_data,
    ) -> None:
        """Forecast should only use pending projections."""
        service = CashflowService(db_session)

        result = await service.build_forecast(
            user_id=cashflow_fixture_data["user_id"],
            target_date=cashflow_fixture_data["future_date"],
        )

        assert result.projected_income == Decimal("500.00")
        assert result.projected_expense == Decimal("300.00")
        assert result.pending_count == 2

    async def test_opening_balance_reflects_updated_historical_transaction(
        self,
        db_session,
        cashflow_fixture_data,
    ) -> None:
        """Opening balance should reflect current actual data on each read."""
        service = CashflowService(db_session)
        opening_income = cashflow_fixture_data["opening_income"]
        opening_income.amount = Decimal("1200.00")
        await db_session.commit()

        result = await service.build_report(
            user_id=cashflow_fixture_data["user_id"],
            from_date=cashflow_fixture_data["report_start"],
            to_date=cashflow_fixture_data["confirmed_date"],
        )

        assert result.opening_balance == Decimal("1200.00")
