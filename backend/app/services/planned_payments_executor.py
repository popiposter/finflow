"""Executor service for scheduler-facing planned payment execution flow."""

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.finance import ProjectionExecutionSummary, ProjectionGenerationResult
from app.services.projection_scheduler_service import ProjectionSchedulerService


class PlannedPaymentsExecutor:
    """Legacy wrapper around projection generation for planned payments."""

    def __init__(self, session: AsyncSession, user_id: str | None = None):
        """Initialize the executor with a database session and optional user scope."""
        self.user_id = UUID(user_id) if user_id is not None else None
        self.generation_service = ProjectionSchedulerService(session)

    async def execute_due_payments(
        self,
        as_of_date: date | None = None,
        max_occurrences: int = 100,
    ) -> ProjectionExecutionSummary:
        """Execute due planned payments for the scoped user and return a summary."""
        if self.user_id is None:
            raise ValueError("PlannedPaymentsExecutor requires a scoped user_id")

        results = await self.generation_service.generate_due_projections(
            user_id=self.user_id,
            as_of_date=as_of_date,
            max_occurrences=max_occurrences,
        )

        if max_occurrences >= 0:
            details: list[ProjectionGenerationResult] = results[:max_occurrences]
        else:
            details = results

        total_generated = sum(len(result.generated_projections) for result in details)
        total_skipped = sum(result.skipped_occurrences for result in details)

        return ProjectionExecutionSummary(
            total_processed=len(details),
            total_generated=total_generated,
            skipped_occurrences=total_skipped,
            details=details,
        )
