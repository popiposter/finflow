"""Scheduler-facing service for generating projected transactions."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planned_payment import PlannedPayment
from app.models.types import CategoryType, ProjectedTransactionType
from app.repositories.category_repository import CategoryRepository
from app.repositories.planned_payment_repository import PlannedPaymentRepository
from app.repositories.projected_transaction_repository import (
    ProjectedTransactionRepository,
)
from app.schemas.finance import ProjectionGenerationResult
from app.services.planned_payment_service import compute_next_due_date


class ProjectionSchedulerService:
    """Generate due projected transactions from planned payment templates."""

    def __init__(self, session: AsyncSession):
        """Initialize the service with a database session."""
        self.session = session
        self.category_repo = CategoryRepository(session)
        self.planned_payment_repo = PlannedPaymentRepository(session)
        self.projected_transaction_repo = ProjectedTransactionRepository(session)

    async def generate_due_projections(
        self,
        user_id: UUID | None = None,
        as_of_date: date | None = None,
        max_occurrences: int = 100,
    ) -> list[ProjectionGenerationResult]:
        """Generate one pending projection per due planned payment occurrence."""
        if as_of_date is None:
            as_of_date = date.today()

        if user_id is not None:
            due_payments = await self.planned_payment_repo.get_due_by_user(
                user_id=user_id,
                as_of_date=as_of_date,
                limit=max_occurrences,
            )
        else:
            due_payments = await self.planned_payment_repo.get_due_planned_payments(
                as_of_date=as_of_date,
                limit=max_occurrences,
            )

        results: list[ProjectionGenerationResult] = []
        for payment in due_payments[:max_occurrences]:
            result = await self._generate_for_planned_payment(payment)
            results.append(result)

        return results

    async def _generate_for_planned_payment(
        self,
        payment: PlannedPayment,
    ) -> ProjectionGenerationResult:
        """Generate a single projected occurrence and advance the template cursor."""
        next_due = compute_next_due_date(
            payment.start_date,
            payment.next_due_at,
            payment.recurrence,
        )

        existing_projection = await self.projected_transaction_repo.get_by_planned_payment_and_origin_date(
            planned_payment_id=payment.id,
            origin_date=payment.next_due_at,
        )
        if existing_projection is not None:
            payment.next_due_at = next_due
            await self.planned_payment_repo.update(payment)
            return ProjectionGenerationResult(
                planned_payment_id=payment.id,
                generated_projections=[],
                next_due_at=next_due,
                skipped_occurrences=1,
            )

        projected_transaction = await self.projected_transaction_repo.create(
            planned_payment_id=payment.id,
            origin_date=payment.next_due_at,
            origin_amount=payment.amount,
            origin_description=payment.description,
            origin_category_id=payment.category_id,
            type_=await self._resolve_projection_type(payment),
            projected_date=payment.next_due_at,
            projected_amount=payment.amount,
            projected_description=payment.description,
            projected_category_id=payment.category_id,
        )

        payment.next_due_at = next_due
        await self.planned_payment_repo.update(payment)

        return ProjectionGenerationResult(
            planned_payment_id=payment.id,
            generated_projections=[projected_transaction.id],
            next_due_at=next_due,
        )

    async def _resolve_projection_type(
        self,
        payment: PlannedPayment,
    ) -> ProjectedTransactionType:
        """Map legacy planned payment data into projection type semantics."""
        if payment.category_id is None:
            return ProjectedTransactionType.EXPENSE

        category = await self.category_repo.get_by_id(payment.category_id)
        if category is not None and category.type == CategoryType.INCOME:
            return ProjectedTransactionType.INCOME

        return ProjectedTransactionType.EXPENSE
