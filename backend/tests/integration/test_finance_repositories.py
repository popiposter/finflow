"""Integration tests for finance repositories.

These tests verify that the account, category, and transaction repositories
work correctly with the PostgreSQL database.
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.types import AccountType, CategoryType, TransactionType
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository


@pytest.mark.integration
class TestAccountRepository:
    """Tests for AccountRepository database operations."""

    async def _create_user(self, db_session: AsyncSession) -> uuid4.__class__:
        """Helper to create a user and return their ID."""
        repo = UserRepository(db_session)
        user = await repo.create(
            email=f"test_{uuid4()}@example.com",
            hashed_password="hashed_password",
        )
        return user.id

    @pytest.mark.asyncio
    async def test_create_account(self, clean_db, db_session: AsyncSession) -> None:
        """Test creating a new account."""
        repo = AccountRepository(db_session)
        user_id = await self._create_user(db_session)

        account = await repo.create(
            user_id=user_id,
            name="Test Checking Account",
            type_=AccountType.CHECKING,
        )

        assert account.id is not None
        assert account.user_id == user_id
        assert account.name == "Test Checking Account"
        assert account.type == AccountType.CHECKING
        assert account.current_balance == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_get_account_by_id(self, clean_db, db_session: AsyncSession) -> None:
        """Test retrieving an account by ID."""
        repo = AccountRepository(db_session)
        user_id = await self._create_user(db_session)

        account = await repo.create(
            user_id=user_id,
            name="Test Account",
            type_=AccountType.SAVINGS,
        )

        retrieved = await repo.get_by_id(account.id)
        assert retrieved is not None
        assert retrieved.id == account.id
        assert retrieved.name == "Test Account"

    @pytest.mark.asyncio
    async def test_get_account_by_user(
        self, clean_db, db_session: AsyncSession
    ) -> None:
        """Test retrieving accounts for a user."""
        repo = AccountRepository(db_session)
        user_id = await self._create_user(db_session)

        await repo.create(
            user_id=user_id,
            name="Account 1",
            type_=AccountType.CHECKING,
        )
        await repo.create(
            user_id=user_id,
            name="Account 2",
            type_=AccountType.SAVINGS,
        )

        accounts = await repo.get_by_user(user_id)
        assert len(accounts) == 2

    @pytest.mark.asyncio
    async def test_update_account(self, clean_db, db_session: AsyncSession) -> None:
        """Test updating an account."""
        repo = AccountRepository(db_session)
        user_id = await self._create_user(db_session)

        account = await repo.create(
            user_id=user_id,
            name="Original Name",
            type_=AccountType.CHECKING,
        )

        account.name = "Updated Name"
        account.current_balance = Decimal("100.50")
        updated = await repo.update(account)

        assert updated.name == "Updated Name"
        assert updated.current_balance == Decimal("100.50")

    @pytest.mark.asyncio
    async def test_delete_account(self, clean_db, db_session: AsyncSession) -> None:
        """Test deleting an account."""
        repo = AccountRepository(db_session)
        user_id = await self._create_user(db_session)

        account = await repo.create(
            user_id=user_id,
            name="To Delete",
            type_=AccountType.CHECKING,
        )

        await repo.delete(account)

        # Verify deletion
        result = await repo.get_by_id(account.id)
        assert result is None


@pytest.mark.integration
class TestCategoryRepository:
    """Tests for CategoryRepository database operations."""

    async def _create_user(self, db_session: AsyncSession) -> uuid4.__class__:
        """Helper to create a user and return their ID."""
        repo = UserRepository(db_session)
        user = await repo.create(
            email=f"test_{uuid4()}@example.com",
            hashed_password="hashed_password",
        )
        return user.id

    @pytest.mark.asyncio
    async def test_create_category(self, clean_db, db_session: AsyncSession) -> None:
        """Test creating a new category."""
        repo = CategoryRepository(db_session)
        user_id = await self._create_user(db_session)

        category = await repo.create(
            user_id=user_id,
            name="Housing",
            type_=CategoryType.EXPENSE,
        )

        assert category.id is not None
        assert category.user_id == user_id
        assert category.name == "Housing"
        assert category.type == CategoryType.EXPENSE

    @pytest.mark.asyncio
    async def test_create_category_with_parent(
        self, clean_db, db_session: AsyncSession
    ) -> None:
        """Test creating a child category with parent."""
        repo = CategoryRepository(db_session)
        user_id = await self._create_user(db_session)

        parent = await repo.create(
            user_id=user_id,
            name="Housing",
            type_=CategoryType.EXPENSE,
        )

        child = await repo.create(
            user_id=user_id,
            name="Rent",
            type_=CategoryType.EXPENSE,
            parent_id=parent.id,
        )

        assert child.parent_id == parent.id
        assert child.name == "Rent"

    @pytest.mark.asyncio
    async def test_get_category_by_id(self, clean_db, db_session: AsyncSession) -> None:
        """Test retrieving a category by ID."""
        repo = CategoryRepository(db_session)
        user_id = await self._create_user(db_session)

        category = await repo.create(
            user_id=user_id,
            name="Food",
            type_=CategoryType.EXPENSE,
        )

        retrieved = await repo.get_by_id(category.id)
        assert retrieved is not None
        assert retrieved.id == category.id

    @pytest.mark.asyncio
    async def test_get_category_by_user(
        self, clean_db, db_session: AsyncSession
    ) -> None:
        """Test retrieving categories for a user."""
        repo = CategoryRepository(db_session)
        user_id = await self._create_user(db_session)

        await repo.create(
            user_id=user_id,
            name="Income",
            type_=CategoryType.INCOME,
        )
        await repo.create(
            user_id=user_id,
            name="Food",
            type_=CategoryType.EXPENSE,
        )

        categories = await repo.get_by_user(user_id)
        assert len(categories) == 2

    @pytest.mark.asyncio
    async def test_get_category_by_type(
        self, clean_db, db_session: AsyncSession
    ) -> None:
        """Test retrieving categories by type."""
        repo = CategoryRepository(db_session)
        user_id = await self._create_user(db_session)

        await repo.create(
            user_id=user_id,
            name="Salary",
            type_=CategoryType.INCOME,
        )
        await repo.create(
            user_id=user_id,
            name="Food",
            type_=CategoryType.EXPENSE,
        )

        income_cats = await repo.get_by_type(user_id, CategoryType.INCOME)
        expense_cats = await repo.get_by_type(user_id, CategoryType.EXPENSE)

        assert len(income_cats) == 1
        assert len(expense_cats) == 1

    @pytest.mark.asyncio
    async def test_get_children(self, clean_db, db_session: AsyncSession) -> None:
        """Test retrieving child categories."""
        repo = CategoryRepository(db_session)
        user_id = await self._create_user(db_session)

        parent = await repo.create(
            user_id=user_id,
            name="Housing",
            type_=CategoryType.EXPENSE,
        )

        await repo.create(
            user_id=user_id,
            name="Rent",
            type_=CategoryType.EXPENSE,
            parent_id=parent.id,
        )
        await repo.create(
            user_id=user_id,
            name="Utilities",
            type_=CategoryType.EXPENSE,
            parent_id=parent.id,
        )

        children = await repo.get_children(parent.id)
        assert len(children) == 2

    @pytest.mark.asyncio
    async def test_update_category(self, clean_db, db_session: AsyncSession) -> None:
        """Test updating a category."""
        repo = CategoryRepository(db_session)
        user_id = await self._create_user(db_session)

        category = await repo.create(
            user_id=user_id,
            name="Original Name",
            type_=CategoryType.EXPENSE,
        )

        category.name = "Updated Name"
        updated = await repo.update(category)

        assert updated.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_category(self, clean_db, db_session: AsyncSession) -> None:
        """Test deleting a category."""
        repo = CategoryRepository(db_session)
        user_id = await self._create_user(db_session)

        category = await repo.create(
            user_id=user_id,
            name="To Delete",
            type_=CategoryType.EXPENSE,
        )

        await repo.delete(category)

        result = await repo.get_by_id(category.id)
        assert result is None


@pytest.mark.integration
class TestTransactionRepository:
    """Tests for TransactionRepository database operations."""

    async def _create_user(self, db_session: AsyncSession) -> uuid4.__class__:
        """Helper to create a user and return their ID."""
        repo = UserRepository(db_session)
        user = await repo.create(
            email=f"test_{uuid4()}@example.com",
            hashed_password="hashed_password",
        )
        return user.id

    async def _create_account(
        self, db_session: AsyncSession, user_id: uuid4.__class__
    ) -> uuid4.__class__:
        """Helper to create an account for a user and return account_id."""
        from app.models.types import AccountType
        from app.repositories.account_repository import AccountRepository

        repo = AccountRepository(db_session)
        account = await repo.create(
            user_id=user_id,
            name="Test Account",
            type_=AccountType.CHECKING,
        )
        account.currency_code = "USD"
        account.current_balance = Decimal("0.00")
        await repo.update(account)
        return account.id

    async def _create_category(
        self, db_session: AsyncSession, user_id: uuid4.__class__
    ) -> uuid4.__class__:
        """Helper to create a category for a user and return category_id."""
        from app.models.types import CategoryType
        from app.repositories.category_repository import CategoryRepository

        repo = CategoryRepository(db_session)
        category = await repo.create(
            user_id=user_id,
            name="Test Category",
            type_=CategoryType.EXPENSE,
        )
        return category.id

    @pytest.mark.asyncio
    async def test_create_transaction(self, clean_db, db_session: AsyncSession) -> None:
        """Test creating a new transaction."""
        repo = TransactionRepository(db_session)
        user_id = await self._create_user(db_session)
        account_id = await self._create_account(db_session, user_id)

        transaction = await repo.create(
            user_id=user_id,
            account_id=account_id,
            amount=Decimal("100.00"),
            type_=TransactionType.PAYMENT,
            date_accrual=datetime(2024, 1, 15, tzinfo=timezone.utc),
            date_cash=datetime(2024, 1, 16, tzinfo=timezone.utc),
        )

        assert transaction.id is not None
        assert transaction.user_id == user_id
        assert transaction.amount == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_create_transaction_with_category(
        self, clean_db, db_session: AsyncSession
    ) -> None:
        """Test creating a transaction with category reference."""
        repo = TransactionRepository(db_session)
        user_id = await self._create_user(db_session)
        account_id = await self._create_account(db_session, user_id)
        category_id = await self._create_category(db_session, user_id)

        transaction = await repo.create(
            user_id=user_id,
            account_id=account_id,
            amount=Decimal("50.00"),
            type_=TransactionType.PAYMENT,
            date_accrual=datetime(2024, 1, 15, tzinfo=timezone.utc),
            date_cash=datetime(2024, 1, 16, tzinfo=timezone.utc),
            category_id=category_id,
        )

        assert transaction.category_id == category_id

    @pytest.mark.asyncio
    async def test_create_transaction_dates(
        self, clean_db, db_session: AsyncSession
    ) -> None:
        """Test that date_accrual and date_cash are stored correctly.

        This validates the accrual vs cash basis accounting support.
        """
        repo = TransactionRepository(db_session)
        user_id = await self._create_user(db_session)
        account_id = await self._create_account(db_session, user_id)

        # Transaction where dates differ (accrual accounting)
        transaction = await repo.create(
            user_id=user_id,
            account_id=account_id,
            amount=Decimal("200.00"),
            type_=TransactionType.INCOME,
            date_accrual=datetime(2024, 1, 31, tzinfo=timezone.utc),
            date_cash=datetime(2024, 2, 5, tzinfo=timezone.utc),  # Cash moves later
        )

        assert transaction.date_accrual.day == 31
        assert transaction.date_cash.day == 5
        assert transaction.date_accrual != transaction.date_cash

    @pytest.mark.asyncio
    async def test_get_transaction_by_id(
        self, clean_db, db_session: AsyncSession
    ) -> None:
        """Test retrieving a transaction by ID."""
        repo = TransactionRepository(db_session)
        user_id = await self._create_user(db_session)
        account_id = await self._create_account(db_session, user_id)

        transaction = await repo.create(
            user_id=user_id,
            account_id=account_id,
            amount=Decimal("75.00"),
            type_=TransactionType.PAYMENT,
            date_accrual=datetime(2024, 1, 15, tzinfo=timezone.utc),
            date_cash=datetime(2024, 1, 16, tzinfo=timezone.utc),
        )

        retrieved = await repo.get_by_id(transaction.id)
        assert retrieved is not None
        assert retrieved.id == transaction.id

    @pytest.mark.asyncio
    async def test_get_transaction_by_user(
        self, clean_db, db_session: AsyncSession
    ) -> None:
        """Test retrieving transactions for a user."""
        repo = TransactionRepository(db_session)
        user_id = await self._create_user(db_session)
        account_id = await self._create_account(db_session, user_id)

        await repo.create(
            user_id=user_id,
            account_id=account_id,
            amount=Decimal("100.00"),
            type_=TransactionType.PAYMENT,
            date_accrual=datetime(2024, 1, 15, tzinfo=timezone.utc),
            date_cash=datetime(2024, 1, 16, tzinfo=timezone.utc),
        )
        await repo.create(
            user_id=user_id,
            account_id=account_id,
            amount=Decimal("50.00"),
            type_=TransactionType.INCOME,
            date_accrual=datetime(2024, 1, 16, tzinfo=timezone.utc),
            date_cash=datetime(2024, 1, 17, tzinfo=timezone.utc),
        )

        transactions = await repo.get_by_user(user_id)
        assert len(transactions) == 2

    @pytest.mark.asyncio
    async def test_get_transaction_by_account(
        self, clean_db, db_session: AsyncSession
    ) -> None:
        """Test retrieving transactions for an account."""
        repo = TransactionRepository(db_session)
        user_id = await self._create_user(db_session)
        account_id = await self._create_account(db_session, user_id)

        await repo.create(
            user_id=user_id,
            account_id=account_id,
            amount=Decimal("100.00"),
            type_=TransactionType.PAYMENT,
            date_accrual=datetime(2024, 1, 15, tzinfo=timezone.utc),
            date_cash=datetime(2024, 1, 16, tzinfo=timezone.utc),
        )
        other_account_id = await self._create_account(
            db_session, user_id
        )  # Different account

        await repo.create(
            user_id=user_id,
            account_id=other_account_id,
            amount=Decimal("50.00"),
            type_=TransactionType.PAYMENT,
            date_accrual=datetime(2024, 1, 16, tzinfo=timezone.utc),
            date_cash=datetime(2024, 1, 17, tzinfo=timezone.utc),
        )

        transactions = await repo.get_by_account(account_id)
        assert len(transactions) == 1

    @pytest.mark.asyncio
    async def test_get_by_date_range(self, clean_db, db_session: AsyncSession) -> None:
        """Test retrieving transactions within a date range.

        This validates date_accrual range filtering for reporting.
        """
        repo = TransactionRepository(db_session)
        user_id = await self._create_user(db_session)
        account_id = await self._create_account(db_session, user_id)

        # Transaction in range
        await repo.create(
            user_id=user_id,
            account_id=account_id,
            amount=Decimal("100.00"),
            type_=TransactionType.PAYMENT,
            date_accrual=datetime(2024, 1, 15, tzinfo=timezone.utc),
            date_cash=datetime(2024, 1, 16, tzinfo=timezone.utc),
        )

        # Transaction before range
        await repo.create(
            user_id=user_id,
            account_id=account_id,
            amount=Decimal("50.00"),
            type_=TransactionType.PAYMENT,
            date_accrual=datetime(2024, 1, 10, tzinfo=timezone.utc),
            date_cash=datetime(2024, 1, 11, tzinfo=timezone.utc),
        )

        # Transaction after range
        await repo.create(
            user_id=user_id,
            account_id=account_id,
            amount=Decimal("75.00"),
            type_=TransactionType.PAYMENT,
            date_accrual=datetime(2024, 1, 20, tzinfo=timezone.utc),
            date_cash=datetime(2024, 1, 21, tzinfo=timezone.utc),
        )

        start_date = datetime(2024, 1, 14, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 16, tzinfo=timezone.utc)

        transactions = await repo.get_by_date_range(user_id, start_date, end_date)
        assert len(transactions) == 1
        assert transactions[0].amount == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_update_transaction(self, clean_db, db_session: AsyncSession) -> None:
        """Test updating a transaction."""
        repo = TransactionRepository(db_session)
        user_id = await self._create_user(db_session)
        account_id = await self._create_account(db_session, user_id)

        transaction = await repo.create(
            user_id=user_id,
            account_id=account_id,
            amount=Decimal("100.00"),
            type_=TransactionType.PAYMENT,
            date_accrual=datetime(2024, 1, 15, tzinfo=timezone.utc),
            date_cash=datetime(2024, 1, 16, tzinfo=timezone.utc),
        )

        transaction.amount = Decimal("150.00")
        transaction.description = "Updated description"
        updated = await repo.update(transaction)

        assert updated.amount == Decimal("150.00")
        assert updated.description == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_transaction(self, clean_db, db_session: AsyncSession) -> None:
        """Test deleting a transaction."""
        repo = TransactionRepository(db_session)
        user_id = await self._create_user(db_session)
        account_id = await self._create_account(db_session, user_id)

        transaction = await repo.create(
            user_id=user_id,
            account_id=account_id,
            amount=Decimal("100.00"),
            type_=TransactionType.PAYMENT,
            date_accrual=datetime(2024, 1, 15, tzinfo=timezone.utc),
            date_cash=datetime(2024, 1, 16, tzinfo=timezone.utc),
        )

        await repo.delete(transaction)

        result = await repo.get_by_id(transaction.id)
        assert result is None


@pytest.mark.integration
class TestCategoryHierarchy:
    """Tests for category hierarchy behavior."""

    async def _create_user(self, db_session: AsyncSession) -> uuid4.__class__:
        """Helper to create a user and return their ID."""
        repo = UserRepository(db_session)
        user = await repo.create(
            email=f"test_{uuid4()}@example.com",
            hashed_password="hashed_password",
        )
        return user.id

    @pytest.mark.asyncio
    async def test_nested_categories(self, clean_db, db_session: AsyncSession) -> None:
        """Test three-level category hierarchy."""
        repo = CategoryRepository(db_session)
        user_id = await self._create_user(db_session)

        # Top level
        food = await repo.create(
            user_id=user_id,
            name="Food",
            type_=CategoryType.EXPENSE,
        )

        # Second level
        groceries = await repo.create(
            user_id=user_id,
            name="Groceries",
            type_=CategoryType.EXPENSE,
            parent_id=food.id,
        )

        # Third level
        produce = await repo.create(
            user_id=user_id,
            name="Produce",
            type_=CategoryType.EXPENSE,
            parent_id=groceries.id,
        )

        # Verify hierarchy
        children = await repo.get_children(groceries.id)
        assert len(children) == 1
        assert children[0].name == "Produce"

        grandchild = await repo.get_by_id(produce.id)
        assert grandchild is not None
        assert grandchild.parent_id == groceries.id

    @pytest.mark.asyncio
    async def test_system_categories(self, clean_db, db_session: AsyncSession) -> None:
        """Test system categories (user_id=NULL) can be created."""
        repo = CategoryRepository(db_session)

        system_cat = await repo.create(
            user_id=None,
            name="System Income",
            type_=CategoryType.INCOME,
        )

        assert system_cat.user_id is None

        # System category should be retrievable
        retrieved = await repo.get_by_id(system_cat.id)
        assert retrieved is not None
