"""Unit tests for finance domain models.

Tests verify model creation, basic validation, and type safety.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.types import AccountType, CategoryType, TransactionType


class TestAccountModel:
    """Tests for Account model creation and validation."""

    def test_create_account_minimum_fields(self) -> None:
        """Test creating an account with required fields only."""
        user_id = uuid4()
        account = Account(
            user_id=user_id,
            name="Test Account",
            type=AccountType.CHECKING,
            current_balance=0.00,
            currency_code="USD",
            is_active=True,
        )

        assert account.user_id == user_id
        assert account.name == "Test Account"
        assert account.type == AccountType.CHECKING
        assert account.current_balance == 0.00
        assert account.currency_code == "USD"
        assert account.is_active is True
        assert account.description is None
        assert account.opened_at is None
        assert account.closed_at is None

    def test_create_account_all_fields(self) -> None:
        """Test creating an account with all optional fields."""
        user_id = uuid4()
        account = Account(
            user_id=user_id,
            name="Savings Account",
            type=AccountType.SAVINGS,
            description="Emergency fund savings",
            current_balance=5000.00,
            currency_code="USD",
            is_active=True,
            opened_at=datetime.now(timezone.utc),
        )

        assert account.user_id == user_id
        assert account.name == "Savings Account"
        assert account.type == AccountType.SAVINGS
        assert account.description == "Emergency fund savings"
        assert account.current_balance == 5000.00
        assert account.currency_code == "USD"
        assert account.is_active is True

    @pytest.mark.parametrize(
        "account_type",
        [
            AccountType.CHECKING,
            AccountType.SAVINGS,
            AccountType.CREDIT_CARD,
            AccountType.CASH,
            AccountType.INVESTMENT,
            AccountType.LOAN,
            AccountType.OTHER,
        ],
    )
    def test_account_type_enum(self, account_type: AccountType) -> None:
        """Test all account types are valid."""
        user_id = uuid4()
        account = Account(
            user_id=user_id,
            name="Test",
            type=account_type,
        )
        assert account.type == account_type


class TestCategoryModel:
    """Tests for Category model creation and validation."""

    def test_create_category_minimum_fields(self) -> None:
        """Test creating a category with required fields only."""
        user_id = uuid4()
        category = Category(
            user_id=user_id,
            name="Test Category",
            type=CategoryType.EXPENSE,
            is_active=True,
            display_order=0,
        )

        assert category.user_id == user_id
        assert category.name == "Test Category"
        assert category.type == CategoryType.EXPENSE
        assert category.description is None
        assert category.parent_id is None
        assert category.is_active is True
        assert category.display_order == 0

    def test_create_category_with_parent(self) -> None:
        """Test creating a sub-category with parent."""
        user_id = uuid4()
        parent_id = uuid4()
        category = Category(
            user_id=user_id,
            name="Sub Category",
            type=CategoryType.EXPENSE,
            parent_id=parent_id,
            display_order=1,
        )

        assert category.parent_id == parent_id
        assert category.display_order == 1

    def test_create_system_category(self) -> None:
        """Test creating a system-level category (no user)."""
        category = Category(
            name="Shared Category",
            type=CategoryType.INCOME,
        )

        assert category.user_id is None
        assert category.name == "Shared Category"

    @pytest.mark.parametrize(
        "category_type",
        [CategoryType.INCOME, CategoryType.EXPENSE],
    )
    def test_category_type_enum(self, category_type: CategoryType) -> None:
        """Test all category types are valid."""
        user_id = uuid4()
        category = Category(
            user_id=user_id,
            name="Test",
            type=category_type,
        )
        assert category.type == category_type


class TestTransactionModel:
    """Tests for Transaction model creation and validation."""

    def test_create_transaction_minimum_fields(self) -> None:
        """Test creating a transaction with required fields only."""
        user_id = uuid4()
        account_id = uuid4()
        transaction = Transaction(
            user_id=user_id,
            account_id=account_id,
            amount=100.00,
            type=TransactionType.PAYMENT,
            date_accrual=datetime.now(timezone.utc),
            date_cash=datetime.now(timezone.utc),
            is_reconciled=False,
        )

        assert transaction.user_id == user_id
        assert transaction.account_id == account_id
        assert transaction.amount == 100.00
        assert transaction.type == TransactionType.PAYMENT
        assert transaction.description is None
        assert transaction.category_id is None
        assert transaction.counterparty_account_id is None
        assert transaction.is_reconciled is False

    def test_create_transaction_all_fields(self) -> None:
        """Test creating a transaction with all optional fields."""
        user_id = uuid4()
        account_id = uuid4()
        category_id = uuid4()
        counterparty_account_id = uuid4()
        transaction = Transaction(
            user_id=user_id,
            account_id=account_id,
            category_id=category_id,
            counterparty_account_id=counterparty_account_id,
            amount=250.75,
            type=TransactionType.TRANSFER,
            description="Monthly transfer to savings",
            date_accrual=datetime.now(timezone.utc),
            date_cash=datetime.now(timezone.utc),
            is_reconciled=True,
        )

        assert transaction.category_id == category_id
        assert transaction.counterparty_account_id == counterparty_account_id
        assert transaction.amount == 250.75
        assert transaction.description == "Monthly transfer to savings"
        assert transaction.is_reconciled is True

    def test_transaction_date_fields(self) -> None:
        """Test transaction date fields can differ (accrual vs cash basis)."""
        user_id = uuid4()
        account_id = uuid4()
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)

        transaction = Transaction(
            user_id=user_id,
            account_id=account_id,
            amount=100.00,
            type=TransactionType.PAYMENT,
            date_accrual=yesterday,  # Accrual date (yesterday)
            date_cash=now,  # Cash date (today)
        )

        assert transaction.date_accrual < transaction.date_cash

    @pytest.mark.parametrize(
        "transaction_type",
        [
            TransactionType.PAYMENT,
            TransactionType.REFUND,
            TransactionType.TRANSFER,
            TransactionType.INCOME,
            TransactionType.EXPENSE,
            TransactionType.ADJUSTMENT,
        ],
    )
    def test_transaction_type_enum(self, transaction_type: TransactionType) -> None:
        """Test all transaction types are valid."""
        user_id = uuid4()
        account_id = uuid4()
        transaction = Transaction(
            user_id=user_id,
            account_id=account_id,
            amount=100.00,
            type=transaction_type,
            date_accrual=datetime.now(timezone.utc),
            date_cash=datetime.now(timezone.utc),
        )
        assert transaction.type == transaction_type
