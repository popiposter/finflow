"""Service for transaction mutations."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import TransactionNotFoundError
from app.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository


class TransactionService:
    """Service for transaction updates."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service dependencies."""
        self.transaction_repo = TransactionRepository(session)
        self.account_repo = AccountRepository(session)
        self.category_repo = CategoryRepository(session)

    async def update_transaction(
        self,
        transaction_id: UUID,
        user_id: UUID,
        *,
        amount: Decimal | None = None,
        category_id: UUID | None = None,
        description: str | None = None,
        date_accrual: datetime | None = None,
        date_cash: datetime | None = None,
        is_reconciled: bool | None = None,
        clear_category: bool = False,
        clear_description: bool = False,
    ) -> Transaction:
        """Apply a partial update to an owned transaction."""
        transaction = await self.transaction_repo.get_by_id(transaction_id)
        if transaction is None or transaction.user_id != user_id:
            raise TransactionNotFoundError(str(transaction_id))

        if clear_category:
            transaction.category_id = None
        elif category_id is not None:
            category = await self.category_repo.get_by_id(category_id)
            if category is None or category.user_id != user_id:
                raise TransactionNotFoundError(str(transaction_id))
            transaction.category_id = category_id

        if amount is not None:
            transaction.amount = amount
        if clear_description:
            transaction.description = None
        elif description is not None:
            transaction.description = description
        if date_accrual is not None:
            transaction.date_accrual = date_accrual
        if date_cash is not None:
            transaction.date_cash = date_cash
        if is_reconciled is not None:
            transaction.is_reconciled = is_reconciled

        return await self.transaction_repo.update(transaction)
