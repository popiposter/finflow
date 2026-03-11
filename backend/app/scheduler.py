"""Application scheduler wiring for recurring projection generation."""

from __future__ import annotations

from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]
from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-untyped]

from app.db.session import async_session_factory
from app.services.projection_scheduler_service import ProjectionSchedulerService


class ProjectionSchedulerManager:
    """Manage APScheduler lifecycle for projection generation."""

    job_id = "projection_generation"

    def __init__(self) -> None:
        """Initialize the scheduler and register jobs."""
        self.scheduler = AsyncIOScheduler(timezone=UTC)
        self.scheduler.add_job(
            self.run_projection_generation,
            trigger=CronTrigger(hour=0, minute=5, timezone=UTC),
            id=self.job_id,
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )

    async def start(self) -> None:
        """Start the scheduler if it is not already running."""
        if not self.scheduler.running:
            self.scheduler.start()

    async def shutdown(self) -> None:
        """Stop the scheduler if it is running."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    async def run_projection_generation(self) -> None:
        """Generate all due projections inside a managed DB session."""
        async with async_session_factory() as session:
            try:
                service = ProjectionSchedulerService(session)
                await service.generate_due_projections()
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    def health(self) -> dict[str, str | None]:
        """Return current scheduler status and next run timestamp."""
        job = self.scheduler.get_job(self.job_id)
        next_run = job.next_run_time if job is not None else None
        return {
            "status": "running" if self.scheduler.running else "stopped",
            "next_run": self._format_datetime(next_run),
        }

    @staticmethod
    def _format_datetime(value: datetime | None) -> str | None:
        """Format scheduler timestamps as UTC ISO 8601 strings."""
        if value is None:
            return None
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
