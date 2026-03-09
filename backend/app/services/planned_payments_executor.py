"""Executor service for scheduler-facing planned payment execution flow."""

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.finance import PlannedPaymentExecutionSummary, RecurrenceGenerationResult
from app.services.planned_payment_service import PlannedPaymentGenerationService


class PlannedPaymentsExecutor:
    """Scheduler-facing wrapper around planned payment generation."""

    def __init__(self, session: AsyncSession, user_id: str | None = None):
        """Initialize the executor with a database session and optional user scope."""
        self.user_id = UUID(user_id) if user_id is not None else None
        self.generation_service = PlannedPaymentGenerationService(session)

    async def execute_due_payments(
        self,
        as_of_date: date | None = None,
        max_occurrences: int = 100,
    ) -> PlannedPaymentExecutionSummary:
        """Execute due planned payments for the scoped user and return a summary."""
        if self.user_id is None:
            raise ValueError("PlannedPaymentsExecutor requires a scoped user_id")

        results = await self.generation_service.generate_due_transactions(
            user_id=self.user_id,
            as_of_date=as_of_date,
        )

        if max_occurrences >= 0:
            details: list[RecurrenceGenerationResult] = results[:max_occurrences]
        else:
            details = results

        total_generated = sum(len(result.generated_transactions) for result in details)
        total_skipped = sum(result.skipped_occurrences for result in details)

        return PlannedPaymentExecutionSummary(
            total_processed=len(details),
            total_generated=total_generated,
            skipped_occurrences=total_skipped,
            details=details,
        )
