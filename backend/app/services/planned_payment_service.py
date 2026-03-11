"""Legacy service for generating recurring transactions from planned payments."""

from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planned_payment import PlannedPayment
from app.models.types import Recurrence, TransactionType
from app.repositories.planned_payment_repository import PlannedPaymentRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.finance import ProjectionGenerationResult


def compute_next_due_date(
    start_date: date,
    current_due: date,
    recurrence: Recurrence,
) -> date:
    """Compute the next due date based on a recurrence rule."""
    match recurrence:
        case Recurrence.DAILY:
            return current_due + timedelta(days=1)
        case Recurrence.WEEKLY:
            return current_due + timedelta(weeks=1)
        case Recurrence.MONTHLY:
            year = current_due.year
            month = current_due.month + 1
            if month > 12:
                month = 1
                year += 1

            if month == 12:
                next_month_last_day = 31
            else:
                next_next_month_first = date(year, month + 1, 1)
                next_month_last_day = (next_next_month_first - timedelta(days=1)).day

            day = min(start_date.day, next_month_last_day)
            return date(year, month, day)
        case _:
            raise ValueError(f"Unknown recurrence: {recurrence}")


class PlannedPaymentGenerationService:
    """Legacy service for generating actual transactions from planned payments.

    This service:
    - Finds planned payments that are due
    - Creates corresponding transactions
    - Updates the next_due_at date for each planned payment
    - Protects against duplicate generation for the same occurrence

    Idempotency is ensured by only generating transactions for planned payments
    where the current next_due_at matches the computed due date for a specific
    occurrence. When a planned payment's recurrence advances, it moves to the
    next computed date, preventing re-generation of the same occurrence.
    """

    def __init__(self, session: AsyncSession):
        """Initialize the service with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.session = session
        self.planned_payment_repo = PlannedPaymentRepository(session)
        self.transaction_repo = TransactionRepository(session)

    async def generate_due_transactions(
        self,
        user_id: UUID | None = None,
        as_of_date: date | None = None,
        max_occurrences: int = 100,
    ) -> list[ProjectionGenerationResult]:
        """Generate transactions for all due planned payments.

        Args:
            user_id: Optional user UUID to scope payments to. If not provided,
                generates for all users.
            as_of_date: The date to check due payments for. Defaults to today.
            max_occurrences: Maximum number of occurrences to process.

        Returns:
            List of generation results for each planned payment processed.
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Get due planned payments, optionally scoped by user
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
            result = await self._generate_for_planned_payment(payment, as_of_date)
            results.append(result)

        return results

    async def _generate_for_planned_payment(
        self,
        payment: PlannedPayment,
        as_of_date: date,
    ) -> ProjectionGenerationResult:
        """Generate transactions for a single planned payment.

        For MVP, we generate exactly one transaction per call for the current
        due date. The next_due_at is updated to the next computed date.

        Args:
            payment: The planned payment to generate for.
            as_of_date: The current date for generation.

        Returns:
            Generation result with transaction IDs and next due date.
        """
        # Compute next due date based on recurrence
        next_due = self._compute_next_due_date(
            payment.start_date,
            payment.next_due_at,
            payment.recurrence,
        )

        # Create the transaction
        transaction = await self.transaction_repo.create(
            user_id=payment.user_id,
            account_id=payment.account_id,
            amount=payment.amount,
            type_=TransactionType.PAYMENT,
            date_accrual=datetime.combine(payment.next_due_at, datetime.min.time()),
            date_cash=datetime.combine(payment.next_due_at, datetime.min.time()),
            category_id=payment.category_id,
            planned_payment_id=payment.id,
            description=payment.description
            or f"Planned payment: {payment.next_due_at}",
            is_reconciled=False,
        )

        # Update planned payment's next due date
        payment.next_due_at = next_due
        await self.planned_payment_repo.update(payment)

        return ProjectionGenerationResult(
            planned_payment_id=payment.id,
            generated_projections=[transaction.id],
            next_due_at=next_due,
        )

    def _compute_next_due_date(
        self,
        start_date: date,
        current_due: date,
        recurrence: Recurrence,
    ) -> date:
        """Compute the next due date based on recurrence rule.

        Args:
            start_date: The original start date of the planned payment.
            current_due: The current due date (next_due_at).
            recurrence: The recurrence pattern.

        Returns:
            The computed next due date.
        """
        return compute_next_due_date(start_date, current_due, recurrence)
