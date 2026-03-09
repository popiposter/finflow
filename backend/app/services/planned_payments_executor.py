"""Executor service for scheduler-facing planned payment execution flow.

This module provides a clean entry point for scheduler orchestration with:
- Idempotent execution behavior
- Clear operational output: what was processed, generated, and skipped
- Reuse of existing generation logic without duplication
"""

from datetime import date, datetime, timedelta
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planned_payment import PlannedPayment
from app.models.transaction import Transaction
from app.models.types import Recurrence, TransactionType
from app.repositories.planned_payment_repository import PlannedPaymentRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.finance import (
    PlannedPaymentExecutionSummary,
    RecurrenceGenerationResult,
)


class DuePaymentInfo(TypedDict):
    """Information about a due planned payment."""

    id: str
    user_id: str
    account_id: str
    amount: float
    recurrence: str
    start_date: str
    next_due_at: str
    category_id: str | None
    description: str | None
    end_date: str | None
    is_active: bool


class PlannedPaymentsExecutor:
    """Executor service for planned payment generation.

    This service provides a scheduler-facing entry point for generating
    recurring transactions from due planned payments. It reuses the
    generation logic from PlannedPaymentGenerationService but provides
    a cleaner API for external orchestration.

    Key features:
    - Idempotent: Running multiple times with the same date won't
      duplicate transactions
    - Clear output: Returns detailed results showing what was processed
      and generated
    - Batch processing: Can process multiple payments in a single run
    """

    def __init__(self, session: AsyncSession):
        """Initialize the executor with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.session = session
        self.planned_payment_repo = PlannedPaymentRepository(session)
        self.transaction_repo = TransactionRepository(session)

    async def execute_due_payments(
        self,
        as_of_date: date | None = None,
        max_occurrences: int = 100,
    ) -> PlannedPaymentExecutionSummary:
        """Execute generation for all due planned payments.

        This is the main entry point for scheduler orchestration. It finds
        all active planned payments that are due as of the given date,
        generates transactions for them, and updates their next_due_at dates.

        Args:
            as_of_date: The date to check due payments for. Defaults to today.
            max_occurrences: Maximum number of occurrences to process in this run.

        Returns:
            An execution summary with:
            - total_processed: Number of planned payments processed
            - total_generated: Number of transactions created
            - skipped_occurrences: Number of skipped occurrences (if any)
            - details: Per-payment generation results
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Get all active planned payments that are due
        due_payments = await self.planned_payment_repo.get_due_planned_payments(
            as_of_date=as_of_date,
            limit=max_occurrences,
        )

        # Debug: Print payment info
        import sys
        print(f"[DEBUG] execute_due_payments: as_of_date={as_of_date}, due_payments count={len(due_payments)}", file=sys.stderr)
        for p in due_payments:
            print(f"[DEBUG]   - payment {p.id}: next_due_at={p.next_due_at}", file=sys.stderr)

        results: list[RecurrenceGenerationResult] = []
        total_generated = 0
        total_skipped = 0

        for payment in due_payments:
            result = await self._generate_for_planned_payment(payment, as_of_date)
            results.append(result)
            total_generated += len(result.generated_transactions)
            total_skipped += result.skipped_occurrences

        return PlannedPaymentExecutionSummary(
            total_processed=len(results),
            total_generated=total_generated,
            skipped_occurrences=total_skipped,
            details=results,
        )

    async def _generate_for_planned_payment(
        self,
        payment: PlannedPayment,
        as_of_date: date,
    ) -> RecurrenceGenerationResult:
        """Generate transactions for a single planned payment.

        This method handles the actual transaction creation for a payment.
        It checks if a transaction already exists for the current next_due_at
        date, and if so, skips generation (idempotent behavior).

        If a new transaction is created, the payment's next_due_at is updated
        to the next computed date.

        Args:
            payment: The planned payment to generate for.
            as_of_date: The current date for generation.

        Returns:
            Generation result with transaction IDs and next due date.
        """
        # Check if transaction already exists for this occurrence
        # Idempotency is handled by checking if a transaction exists for
        # this payment's next_due_at date before creating a new one.
        # We look for a transaction with the same planned_payment_id and date_cash.
        existing_tx_stmt = (
            select(1)
            .where(
                Transaction.planned_payment_id == payment.id,
                Transaction.date_cash == datetime.combine(
                    payment.next_due_at, datetime.min.time()
                ),
            )
            .limit(1)
        )

        result = await self.session.execute(existing_tx_stmt)
        existing_tx = result.scalar_one_or_none()

        if existing_tx is not None:
            # Transaction already exists - this is idempotent re-run
            # Don't update next_due_at, just report the existing transaction
            return RecurrenceGenerationResult(
                planned_payment_id=payment.id,
                generated_transactions=[],
                next_due_at=payment.next_due_at,
                skipped_occurrences=1,
            )

        # No existing transaction - proceed with generation
        # Compute next due date based on recurrence
        next_due = self._compute_next_due_date(
            payment.start_date,
            payment.next_due_at,
            payment.recurrence,
        )

        # Create the transaction
        # Use PAYMENT type since we're generating recurring payment transactions
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

        return RecurrenceGenerationResult(
            planned_payment_id=payment.id,
            generated_transactions=[transaction.id],
            next_due_at=next_due,
            skipped_occurrences=0,
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
        match recurrence:
            case Recurrence.DAILY:
                return current_due + timedelta(days=1)
            case Recurrence.WEEKLY:
                return current_due + timedelta(weeks=1)
            case Recurrence.MONTHLY:
                # Handle month-end edge cases
                year = current_due.year
                month = current_due.month + 1
                if month > 12:
                    month = 1
                    year += 1

                # Get the last day of the target month
                if month == 12:
                    next_month_last_day = 31
                else:
                    # Get first day of next next month, then subtract one day
                    next_next_month_first = date(year, month + 1, 1)
                    next_month_last_day = (
                        next_next_month_first - timedelta(days=1)
                    ).day

                # Use the same day as start_date if possible,
                # or the last day of month if start day doesn't exist
                day = min(start_date.day, next_month_last_day)

                return date(year, month, day)
            case _:
                # Should not happen with enum validation
                raise ValueError(f"Unknown recurrence: {recurrence}")
