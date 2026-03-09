"""Transaction repository for database access."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.models.types import TransactionType


class TransactionRepository:
    """Repository for transaction database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.session = session

    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        """Get a transaction by ID.

        Args:
            transaction_id: The transaction's UUID.

        Returns:
            The transaction if found, None otherwise.
        """
        stmt = select(Transaction).where(Transaction.id == transaction_id)
        result = await self.session.scalar(stmt)
        return result

    async def get_by_user(self, user_id: UUID) -> list[Transaction]:
        """Get all transactions for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            List of transactions for the user.
        """
        stmt = select(Transaction).where(Transaction.user_id == user_id)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_by_account(self, account_id: UUID) -> list[Transaction]:
        """Get all transactions for an account.

        Args:
            account_id: The account's UUID.

        Returns:
            List of transactions for the account.
        """
        stmt = select(Transaction).where(Transaction.account_id == account_id)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_by_date_range(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[Transaction]:
        """Get transactions within a date range.

        Searches both date_accrual and date_cash fields.

        Args:
            user_id: The user's UUID.
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).

        Returns:
            List of transactions in the date range.
        """
        stmt = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.date_accrual >= start_date,
            Transaction.date_accrual <= end_date,
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_unreconciled(self, user_id: UUID) -> list[Transaction]:
        """Get unreconciled transactions for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            List of unreconciled transactions.
        """
        stmt = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.is_reconciled == False,  # noqa: E712
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        user_id: UUID,
        account_id: UUID,
        amount: Decimal,
        type_: TransactionType,
        date_accrual: datetime,
        date_cash: datetime,
        category_id: UUID | None = None,
        counterparty_account_id: UUID | None = None,
        description: str | None = None,
        is_reconciled: bool = False,
    ) -> Transaction:
        """Create a new transaction.

        Args:
            user_id: The user's UUID.
            account_id: The account being affected.
            amount: The transaction amount.
            type_: The transaction type.
            date_accrual: When the transaction is recognized (accounting).
            date_cash: When cash actually moves.
            category_id: Optional category for classification.
            counterparty_account_id: Optional opposing account (transfers).
            description: Human-readable description.
            is_reconciled: Whether transaction is reconciled.

        Returns:
            The created transaction.
        """
        transaction = Transaction(
            user_id=user_id,
            account_id=account_id,
            amount=amount,
            type=type_,
            date_accrual=date_accrual,
            date_cash=date_cash,
            category_id=category_id,
            counterparty_account_id=counterparty_account_id,
            description=description,
            is_reconciled=is_reconciled,
        )
        self.session.add(transaction)
        await self.session.flush()
        await self.session.refresh(transaction)
        return transaction

    async def update(self, transaction: Transaction) -> Transaction:
        """Update a transaction.

        Args:
            transaction: The transaction to update.

        Returns:
            The updated transaction.
        """
        await self.session.flush()
        return transaction

    async def delete(self, transaction: Transaction) -> None:
        """Delete a transaction.

        Args:
            transaction: The transaction to delete.
        """
        await self.session.delete(transaction)
        await self.session.flush()
