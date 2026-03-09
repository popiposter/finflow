"""Planned payment repository for database access."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planned_payment import PlannedPayment
from app.models.types import Recurrence


class PlannedPaymentRepository:
    """Repository for planned payment database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.session = session

    async def get_by_id(self, planned_payment_id: UUID) -> PlannedPayment | None:
        """Get a planned payment by ID.

        Args:
            planned_payment_id: The planned payment's UUID.

        Returns:
            The planned payment if found, None otherwise.
        """
        stmt = select(PlannedPayment).where(PlannedPayment.id == planned_payment_id)
        result = await self.session.scalar(stmt)
        return result

    async def get_by_user(self, user_id: UUID) -> list[PlannedPayment]:
        """Get all planned payments for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            List of planned payments for the user.
        """
        stmt = (
            select(PlannedPayment)
            .where(PlannedPayment.user_id == user_id)
            .order_by(PlannedPayment.next_due_at)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_active_by_user(self, user_id: UUID) -> list[PlannedPayment]:
        """Get all active planned payments for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            List of active planned payments for the user.
        """
        stmt = (
            select(PlannedPayment)
            .where(
                PlannedPayment.user_id == user_id,
                PlannedPayment.is_active == True,  # noqa: E712
            )
            .order_by(PlannedPayment.next_due_at)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_due_planned_payments(
        self,
        as_of_date: date | None = None,
        limit: int = 100,
    ) -> list[PlannedPayment]:
        """Get planned payments that are due as of a given date.

        Args:
            as_of_date: The date to check due payments for. Defaults to today.
            limit: Maximum number of results to return.

        Returns:
            List of planned payments that are due.
        """
        if as_of_date is None:
            as_of_date = date.today()

        stmt = (
            select(PlannedPayment)
            .where(
                PlannedPayment.is_active == True,  # noqa: E712
                PlannedPayment.next_due_at <= as_of_date,
            )
            .order_by(
                PlannedPayment.next_due_at,
                PlannedPayment.created_at,
            )
            .limit(limit)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_by_user_and_id(
        self,
        user_id: UUID,
        planned_payment_id: UUID,
    ) -> PlannedPayment | None:
        """Get a specific planned payment by user and ID.

        Args:
            user_id: The user's UUID.
            planned_payment_id: The planned payment's UUID.

        Returns:
            The planned payment if found, None otherwise.
        """
        stmt = select(PlannedPayment).where(
            PlannedPayment.user_id == user_id,
            PlannedPayment.id == planned_payment_id,
        )
        result = await self.session.scalar(stmt)
        return result

    async def create(
        self,
        user_id: UUID,
        account_id: UUID,
        amount: Decimal,
        recurrence: Recurrence,
        start_date: date,
        next_due_at: date,
        category_id: UUID | None = None,
        description: str | None = None,
        end_date: date | None = None,
        is_active: bool = True,
    ) -> PlannedPayment:
        """Create a new planned payment.

        Args:
            user_id: The user's UUID.
            account_id: The account this planned payment affects.
            amount: The amount for each occurrence.
            recurrence: The recurrence pattern.
            start_date: When the planned payment starts.
            next_due_at: The first due date.
            category_id: Optional category for classification.
            description: Human-readable description.
            end_date: Optional end date.
            is_active: Whether the plan is active.

        Returns:
            The created planned payment.
        """
        planned_payment = PlannedPayment(
            user_id=user_id,
            account_id=account_id,
            amount=amount,
            recurrence=recurrence,
            start_date=start_date,
            next_due_at=next_due_at,
            category_id=category_id,
            description=description,
            end_date=end_date,
            is_active=is_active,
        )
        self.session.add(planned_payment)
        await self.session.flush()
        await self.session.refresh(planned_payment)
        return planned_payment

    async def update(self, planned_payment: PlannedPayment) -> PlannedPayment:
        """Update a planned payment.

        Args:
            planned_payment: The planned payment to update.

        Returns:
            The updated planned payment.
        """
        await self.session.flush()
        await self.session.refresh(planned_payment)
        return planned_payment

    async def delete(self, planned_payment: PlannedPayment) -> None:
        """Delete a planned payment.

        Args:
            planned_payment: The planned payment to delete.
        """
        await self.session.delete(planned_payment)
        await self.session.flush()

    async def deactivate(
        self,
        planned_payment: PlannedPayment,
    ) -> PlannedPayment:
        """Deactivate a planned payment (soft delete).

        Args:
            planned_payment: The planned payment to deactivate.

        Returns:
            The deactivated planned payment.
        """
        planned_payment.is_active = False
        await self.session.flush()
        await self.session.refresh(planned_payment)
        return planned_payment
