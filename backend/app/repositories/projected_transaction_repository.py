"""Projected transaction repository for database access."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.projected_transaction import ProjectedTransaction
from app.models.types import ProjectedTransactionStatus, ProjectedTransactionType


class ProjectedTransactionRepository:
    """Repository for projected transaction database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.session = session

    async def get_by_id(self, projected_transaction_id: UUID) -> ProjectedTransaction | None:
        """Get a projected transaction by ID.

        Args:
            projected_transaction_id: The projected transaction's UUID.

        Returns:
            The projected transaction if found, None otherwise.
        """
        stmt = select(ProjectedTransaction).where(
            ProjectedTransaction.id == projected_transaction_id
        ).options(selectinload(ProjectedTransaction.planned_payment))
        result = await self.session.scalar(stmt)
        return result

    async def get_by_user(self, user_id: UUID) -> list[ProjectedTransaction]:
        """Get all projected transactions for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            List of projected transactions for the user.
        """
        stmt = (
            select(ProjectedTransaction)
            .where(ProjectedTransaction.planned_payment.has(user_id=user_id))
            .options(selectinload(ProjectedTransaction.planned_payment))
            .order_by(ProjectedTransaction.projected_date)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_by_planned_payment(
        self,
        planned_payment_id: UUID,
    ) -> list[ProjectedTransaction]:
        """Get all projected transactions for a planned payment.

        Args:
            planned_payment_id: The planned payment's UUID.

        Returns:
            List of projected transactions for the planned payment.
        """
        stmt = (
            select(ProjectedTransaction)
            .where(
                ProjectedTransaction.planned_payment_id == planned_payment_id
            )
            .options(selectinload(ProjectedTransaction.planned_payment))
            .order_by(ProjectedTransaction.projected_date)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_pending_by_planned_payment(
        self,
        planned_payment_id: UUID,
    ) -> list[ProjectedTransaction]:
        """Get pending projected transactions for a planned payment.

        Args:
            planned_payment_id: The planned payment's UUID.

        Returns:
            List of pending projected transactions for the planned payment.
        """
        stmt = (
            select(ProjectedTransaction)
            .where(
                ProjectedTransaction.planned_payment_id == planned_payment_id,
                ProjectedTransaction.status == ProjectedTransactionStatus.PENDING,
            )
            .options(selectinload(ProjectedTransaction.planned_payment))
            .order_by(ProjectedTransaction.projected_date)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_by_user_and_id(
        self,
        user_id: UUID,
        projected_transaction_id: UUID,
    ) -> ProjectedTransaction | None:
        """Get a specific projected transaction by user and ID.

        Args:
            user_id: The user's UUID.
            projected_transaction_id: The projected transaction's UUID.

        Returns:
            The projected transaction if found, None otherwise.
        """
        stmt = select(ProjectedTransaction).where(
            ProjectedTransaction.planned_payment.has(user_id=user_id),
            ProjectedTransaction.id == projected_transaction_id,
        ).options(selectinload(ProjectedTransaction.planned_payment))
        result = await self.session.scalar(stmt)
        return result

    async def get_filtered(
        self,
        user_id: UUID,
        status: ProjectedTransactionStatus | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[ProjectedTransaction]:
        """Get projected transactions for a user with optional filters.

        Args:
            user_id: The user's UUID.
            status: Filter by status (optional).
            from_date: Filter by from date (optional).
            to_date: Filter by to date (optional).

        Returns:
            List of projected transactions matching the filters.
        """
        stmt = select(ProjectedTransaction).where(
            ProjectedTransaction.planned_payment.has(user_id=user_id)
        ).options(selectinload(ProjectedTransaction.planned_payment))
        if status is not None:
            stmt = stmt.where(ProjectedTransaction.status == status)
        if from_date is not None:
            stmt = stmt.where(ProjectedTransaction.projected_date >= from_date)
        if to_date is not None:
            stmt = stmt.where(ProjectedTransaction.projected_date <= to_date)
        stmt = stmt.order_by(ProjectedTransaction.projected_date)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        planned_payment_id: UUID,
        origin_date: date,
        origin_amount: Decimal,
        origin_description: str | None,
        origin_category_id: UUID | None,
        type_: ProjectedTransactionType,
        projected_date: date,
        projected_amount: Decimal,
        projected_description: str | None,
        projected_category_id: UUID | None,
    ) -> ProjectedTransaction:
        """Create a new projected transaction.

        Args:
            planned_payment_id: The planned payment's UUID.
            origin_date: The occurrence date (snapshot at generation time).
            origin_amount: The original amount (snapshot at generation time).
            origin_description: The original description (snapshot at generation time).
            origin_category_id: The original category_id (snapshot at generation time).
            type_: The transaction type (INCOME or EXPENSE).
            projected_date: The projected date (editable).
            projected_amount: The projected amount (editable).
            projected_description: The projected description (editable).
            projected_category_id: The projected category_id (editable).

        Returns:
            The created projected transaction.
        """
        projected_transaction = ProjectedTransaction(
            planned_payment_id=planned_payment_id,
            origin_date=origin_date,
            origin_amount=origin_amount,
            origin_description=origin_description,
            origin_category_id=origin_category_id,
            type=type_,
            projected_date=projected_date,
            projected_amount=projected_amount,
            projected_description=projected_description,
            projected_category_id=projected_category_id,
            status=ProjectedTransactionStatus.PENDING,
        )
        self.session.add(projected_transaction)
        await self.session.flush()
        await self.session.refresh(projected_transaction)
        return projected_transaction

    async def update(self, projected_transaction: ProjectedTransaction) -> ProjectedTransaction:
        """Update a projected transaction.

        Args:
            projected_transaction: The projected transaction to update.

        Returns:
            The updated projected transaction.
        """
        self.session.add(projected_transaction)
        await self.session.flush()
        await self.session.refresh(projected_transaction)
        return projected_transaction

    async def delete(self, projected_transaction: ProjectedTransaction) -> None:
        """Delete a projected transaction.

        Args:
            projected_transaction: The projected transaction to delete.
        """
        await self.session.delete(projected_transaction)
        await self.session.flush()

    async def confirm_projection(
        self,
        projected_transaction: ProjectedTransaction,
        transaction_id: UUID,
        resolved_at: datetime,
    ) -> ProjectedTransaction:
        """Confirm a projected transaction (mark as CONFIRMED with transaction link).

        Args:
            projected_transaction: The projected transaction to confirm.
            transaction_id: The ID of the created transaction.
            resolved_at: When the projection was resolved.

        Returns:
            The updated projected transaction.
        """
        projected_transaction.status = ProjectedTransactionStatus.CONFIRMED
        projected_transaction.transaction_id = transaction_id
        projected_transaction.resolved_at = resolved_at
        projected_transaction.version += 1
        await self.session.flush()
        await self.session.refresh(projected_transaction)
        return projected_transaction

    async def skip_projection(
        self,
        projected_transaction: ProjectedTransaction,
        resolved_at: datetime,
    ) -> ProjectedTransaction:
        """Skip a projected transaction.

        Args:
            projected_transaction: The projected transaction to skip.
            resolved_at: When the projection was resolved.

        Returns:
            The updated projected transaction.
        """
        projected_transaction.status = ProjectedTransactionStatus.SKIPPED
        projected_transaction.resolved_at = resolved_at
        projected_transaction.version += 1
        await self.session.flush()
        await self.session.refresh(projected_transaction)
        return projected_transaction
