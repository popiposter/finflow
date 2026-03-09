"""Unit tests for report service and aggregation logic."""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.types import AccountType, CategoryType, TransactionType
from app.models.user import User
from app.repositories.report_repository import ReportRepository
from app.schemas.finance import (
    CashflowQueryParams,
    PnLQueryParams,
)
from app.services.report_service import ReportService


@pytest_asyncio.fixture
async def test_user_account_category(
    db_session: AsyncSession,
) -> dict:
    """Create a test user, account, and category."""
    user_id = uuid4()

    # Create user first
    user = User(
        id=user_id,
        email="reporttest@example.com",
        hashed_password="hashedpassword123",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    account = Account(
        user_id=user_id,
        name="Test Checking",
        type=AccountType.CHECKING,
        currency_code="USD",
        current_balance=Decimal("0.00"),
    )
    db_session.add(account)
    await db_session.flush()

    category = Category(
        user_id=user_id,
        name="Housing",
        type=CategoryType.EXPENSE,
    )
    db_session.add(category)
    await db_session.flush()

    await db_session.commit()

    yield {
        "user_id": user_id,
        "account_id": account.id,
        "category_id": category.id,
    }

    await db_session.delete(category)
    await db_session.delete(account)
    await db_session.delete(user)
    await db_session.commit()


@pytest_asyncio.fixture
async def sample_transactions(
    db_session: AsyncSession,
    test_user_account_category: dict,
) -> None:
    """Create sample transactions for testing."""
    user_id = test_user_account_category["user_id"]
    account_id = test_user_account_category["account_id"]
    category_id = test_user_account_category["category_id"]

    # Create transactions with different dates and types
    transactions = [
        # Income transaction
        Transaction(
            user_id=user_id,
            account_id=account_id,
            category_id=category_id,
            amount=Decimal("1000.00"),
            type=TransactionType.INCOME,
            description="Salary",
            date_accrual=datetime(2024, 1, 15, 10, 0, 0),
            date_cash=datetime(2024, 1, 15, 10, 0, 0),
        ),
        # Expense transaction
        Transaction(
            user_id=user_id,
            account_id=account_id,
            category_id=category_id,
            amount=Decimal("500.00"),
            type=TransactionType.EXPENSE,
            description="Rent",
            date_accrual=datetime(2024, 1, 20, 10, 0, 0),
            date_cash=datetime(2024, 1, 20, 10, 0, 0),
        ),
        # Transaction in different category
        Transaction(
            user_id=user_id,
            account_id=account_id,
            category_id=None,  # No category
            amount=Decimal("200.00"),
            type=TransactionType.PAYMENT,
            description="Utilities",
            date_accrual=datetime(2024, 1, 25, 10, 0, 0),
            date_cash=datetime(2024, 1, 25, 10, 0, 0),
        ),
        # Transaction outside date range
        Transaction(
            user_id=user_id,
            account_id=account_id,
            category_id=category_id,
            amount=Decimal("300.00"),
            type=TransactionType.INCOME,
            description="Bonus",
            date_accrual=datetime(2024, 2, 15, 10, 0, 0),
            date_cash=datetime(2024, 2, 15, 10, 0, 0),
        ),
    ]

    for txn in transactions:
        db_session.add(txn)
    await db_session.commit()


class TestReportRepository:
    """Tests for ReportRepository aggregation logic."""

    @pytest_asyncio.fixture
    def report_repo(self, db_session: AsyncSession) -> ReportRepository:
        """Create ReportRepository instance."""
        return ReportRepository(db_session)

    async def test_aggregate_pl_by_date_range(
        self,
        db_session: AsyncSession,
        test_user_account_category: dict,
        sample_transactions: None,
    ) -> None:
        """Test P&L aggregation with date range filter."""
        user_id = test_user_account_category["user_id"]
        repo = ReportRepository(db_session)

        # Query for January 2024 only
        result = await repo.aggregate_pl(
            user_id=user_id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        # Should have 2 transactions in January (income 1000, expense 500)
        # Grand total should be sum of absolute values: 1000 + 500 + 200 = 1700
        assert result["grand_total"] == Decimal("1700.00")

        # Should have category totals
        assert len(result["totals_by_category"]) >= 1

    async def test_aggregate_pl_empty_range(
        self,
        db_session: AsyncSession,
        test_user_account_category: dict,
        sample_transactions: None,
    ) -> None:
        """Test P&L aggregation returns empty for out-of-range dates."""
        user_id = test_user_account_category["user_id"]
        repo = ReportRepository(db_session)

        # Query for February only - should not include January transactions
        result = await repo.aggregate_pl(
            user_id=user_id,
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 28),
        )

        # Should have only the February transaction (300)
        assert result["grand_total"] == Decimal("300.00")

    async def test_aggregate_cashflow_by_date_range(
        self,
        db_session: AsyncSession,
        test_user_account_category: dict,
        sample_transactions: None,
    ) -> None:
        """Test cashflow aggregation with date range filter."""
        user_id = test_user_account_category["user_id"]
        repo = ReportRepository(db_session)

        # Query for January 2024
        result = await repo.aggregate_cashflow(
            user_id=user_id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        # Should have same transactions as P&L for January
        assert result["grand_total"] == Decimal("1700.00")

    async def test_aggregate_cashflow_empty_range(
        self,
        db_session: AsyncSession,
        test_user_account_category: dict,
        sample_transactions: None,
    ) -> None:
        """Test cashflow aggregation returns empty for out-of-range dates."""
        user_id = test_user_account_category["user_id"]
        repo = ReportRepository(db_session)

        # Query for dates before any transactions
        result = await repo.aggregate_cashflow(
            user_id=user_id,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
        )

        # Should be empty
        assert result["grand_total"] == Decimal("0.00")
        assert len(result["totals_by_category"]) == 0
        assert len(result["totals_by_type"]) == 0

    async def test_aggregate_pl_no_transactions(
        self,
        db_session: AsyncSession,
        test_user_account_category: dict,
    ) -> None:
        """Test P&L aggregation with no transactions."""
        user_id = test_user_account_category["user_id"]
        repo = ReportRepository(db_session)

        result = await repo.aggregate_pl(
            user_id=user_id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        assert result["grand_total"] == Decimal("0.00")
        assert result["totals_by_category"] == []
        assert result["totals_by_type"] == []


class TestReportService:
    """Tests for ReportService integration."""

    @pytest_asyncio.fixture
    async def report_service(self, db_session: AsyncSession) -> ReportService:
        """Create ReportService instance."""
        return ReportService(db_session)

    async def test_get_pl_report_response(
        self,
        db_session: AsyncSession,
        test_user_account_category: dict,
        sample_transactions: None,
    ) -> None:
        """Test P&L report response structure."""
        user_id = test_user_account_category["user_id"]
        service = ReportService(db_session)

        params = PnLQueryParams(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        result = await service.get_pl_report(user_id=user_id, query_params=params)

        # Response structure checks
        assert result.date_accrual_start == date(2024, 1, 1)
        assert result.date_accrual_end == date(2024, 1, 31)
        assert result.grand_total == Decimal("1700.00")
        assert len(result.totals_by_category) > 0
        assert len(result.totals_by_type) > 0

        # Check category total structure
        cat_total = result.totals_by_category[0]
        assert hasattr(cat_total, "category_id")
        assert hasattr(cat_total, "category_name")
        assert hasattr(cat_total, "total")
        assert hasattr(cat_total, "type")

    async def test_get_pl_report_empty_range(
        self,
        db_session: AsyncSession,
        test_user_account_category: dict,
        sample_transactions: None,
    ) -> None:
        """Test P&L report for empty date range."""
        user_id = test_user_account_category["user_id"]
        service = ReportService(db_session)

        params = PnLQueryParams(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
        )

        result = await service.get_pl_report(user_id=user_id, query_params=params)

        assert result.grand_total == Decimal("0.00")
        assert result.totals_by_category == []
        assert result.totals_by_type == []

    async def test_get_cashflow_report_response(
        self,
        db_session: AsyncSession,
        test_user_account_category: dict,
        sample_transactions: None,
    ) -> None:
        """Test cashflow report response structure."""
        user_id = test_user_account_category["user_id"]
        service = ReportService(db_session)

        params = CashflowQueryParams(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        result = await service.get_cashflow_report(
            user_id=user_id,
            query_params=params,
        )

        assert result.date_cash_start == date(2024, 1, 1)
        assert result.date_cash_end == date(2024, 1, 31)
        assert result.grand_total == Decimal("1700.00")
        assert len(result.totals_by_category) > 0
