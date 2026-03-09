"""Planned payments API routes."""

from datetime import date
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import get_current_user
from app.repositories.planned_payment_repository import PlannedPaymentRepository
from app.schemas.auth import UserOut
from app.schemas.finance import (
    PlannedPaymentCreate,
    PlannedPaymentExecutionSummary,
    PlannedPaymentOut,
    RecurrenceGenerationResult,
)
from app.services.planned_payment_service import PlannedPaymentGenerationService
from app.services.planned_payments_executor import PlannedPaymentsExecutor

router = APIRouter(prefix="/planned-payments", tags=["planned-payments"])


async def get_planned_payment_repo(
    user: UserOut = Depends(get_current_user),
) -> AsyncGenerator[PlannedPaymentRepository, None]:
    """Get planned payment repository with database session.

    Args:
        user: Current authenticated user.

    Yields:
        PlannedPaymentRepository instance.
    """
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            yield PlannedPaymentRepository(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_generation_service() -> AsyncGenerator[
    PlannedPaymentGenerationService, None
]:
    """Get generation service with database session.

    Yields:
        PlannedPaymentGenerationService instance.
    """
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            yield PlannedPaymentGenerationService(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_executor() -> AsyncGenerator[PlannedPaymentsExecutor, None]:
    """Get executor service with database session.

    Yields:
        PlannedPaymentsExecutor instance.
    """
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            yield PlannedPaymentsExecutor(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@router.post(
    "",
    response_model=PlannedPaymentOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_planned_payment(
    payment_data: PlannedPaymentCreate,
    current_user: UserOut = Depends(get_current_user),
    repo: PlannedPaymentRepository = Depends(get_planned_payment_repo),
) -> PlannedPaymentOut:
    """Create a new planned payment.

    Args:
        payment_data: Planned payment creation data.
        current_user: Authenticated user.
        repo: Planned payment repository dependency.

    Returns:
        Created planned payment.

    Raises:
        HTTPException 400: If validation fails.
    """
    payment = await repo.create(
        user_id=current_user.id,
        account_id=payment_data.account_id,
        amount=payment_data.amount,
        recurrence=payment_data.recurrence,
        start_date=payment_data.start_date,
        next_due_at=payment_data.next_due_at or payment_data.start_date,
        category_id=payment_data.category_id,
        description=payment_data.description,
        end_date=payment_data.end_date,
        is_active=payment_data.is_active,
    )

    return PlannedPaymentOut.model_validate(payment)


@router.get(
    "",
    response_model=list[PlannedPaymentOut],
)
async def list_planned_payments(
    current_user: UserOut = Depends(get_current_user),
    repo: PlannedPaymentRepository = Depends(get_planned_payment_repo),
) -> list[PlannedPaymentOut]:
    """List all active planned payments for the current user.

    Args:
        current_user: Authenticated user.
        repo: Planned payment repository dependency.

    Returns:
        List of active planned payments.
    """
    payments = await repo.get_active_by_user(current_user.id)
    return [PlannedPaymentOut.model_validate(p) for p in payments]


@router.get(
    "/{payment_id}",
    response_model=PlannedPaymentOut,
)
async def get_planned_payment(
    payment_id: str,
    current_user: UserOut = Depends(get_current_user),
    repo: PlannedPaymentRepository = Depends(get_planned_payment_repo),
) -> PlannedPaymentOut:
    """Get a specific planned payment by ID.

    Args:
        payment_id: The planned payment's UUID (as string).
        current_user: Authenticated user.
        repo: Planned payment repository dependency.

    Returns:
        The planned payment.

    Raises:
        HTTPException 404: If planned payment not found or not owned by user.
    """
    from uuid import UUID

    payment_id_uuid = UUID(payment_id)
    payment = await repo.get_by_user_and_id(current_user.id, payment_id_uuid)

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planned payment not found",
        )

    return PlannedPaymentOut.model_validate(payment)


@router.put(
    "/{payment_id}",
    response_model=PlannedPaymentOut,
)
async def update_planned_payment(
    payment_id: str,
    payment_data: PlannedPaymentCreate,
    current_user: UserOut = Depends(get_current_user),
    repo: PlannedPaymentRepository = Depends(get_planned_payment_repo),
) -> PlannedPaymentOut:
    """Update a planned payment.

    Args:
        payment_id: The planned payment's UUID (as string).
        payment_data: Planned payment update data.
        current_user: Authenticated user.
        repo: Planned payment repository dependency.

    Returns:
        Updated planned payment.

    Raises:
        HTTPException 404: If planned payment not found or not owned by user.
    """
    from uuid import UUID

    payment_id_uuid = UUID(payment_id)
    payment = await repo.get_by_user_and_id(current_user.id, payment_id_uuid)

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planned payment not found",
        )

    # Update fields
    payment.account_id = payment_data.account_id
    payment.category_id = payment_data.category_id
    payment.amount = payment_data.amount
    payment.description = payment_data.description
    payment.recurrence = payment_data.recurrence
    payment.start_date = payment_data.start_date
    payment.end_date = payment_data.end_date
    payment.is_active = payment_data.is_active

    await repo.update(payment)
    return PlannedPaymentOut.model_validate(payment)


@router.delete(
    "/{payment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_planned_payment(
    payment_id: str,
    current_user: UserOut = Depends(get_current_user),
    repo: PlannedPaymentRepository = Depends(get_planned_payment_repo),
) -> None:
    """Delete a planned payment (soft delete via is_active=false).

    Args:
        payment_id: The planned payment's UUID (as string).
        current_user: Authenticated user.
        repo: Planned payment repository dependency.

    Raises:
        HTTPException 404: If planned payment not found or not owned by user.
    """
    from uuid import UUID

    payment_id_uuid = UUID(payment_id)
    payment = await repo.get_by_user_and_id(current_user.id, payment_id_uuid)

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planned payment not found",
        )

    await repo.deactivate(payment)


@router.post(
    "/generate",
    response_model=list[RecurrenceGenerationResult],
)
async def generate_transactions(
    generation_service: PlannedPaymentGenerationService = Depends(
        get_generation_service
    ),
    as_of_date: date | None = None,
) -> list[RecurrenceGenerationResult]:
    """Generate transactions for all due planned payments.

    This endpoint finds all active planned payments that are due as of
    the given date and creates corresponding transactions. It updates
    the next_due_at date for each planned payment to the next computed
    occurrence date.

    Args:
        generation_service: Generation service dependency.
        as_of_date: Optional date to check due payments for. Defaults to today.

    Returns:
        List of generation results for each planned payment processed.
    """
    results = await generation_service.generate_due_transactions(
        as_of_date=as_of_date,
    )
    return results


@router.post(
    "/execute",
    response_model=PlannedPaymentExecutionSummary,
)
async def execute_due_payments(
    current_user: UserOut = Depends(get_current_user),
    executor: PlannedPaymentsExecutor = Depends(get_executor),
    as_of_date: date | None = None,
    max_occurrences: int = 100,
) -> PlannedPaymentExecutionSummary:
    """Execute generation for all due planned payments.

    This is the scheduler-facing entry point for generating recurring
    transactions. It provides a clear operational summary of what was
    processed and generated.

    Args:
        executor: Executor service dependency.
        as_of_date: Optional date to check due payments for. Defaults to today.
        max_occurrences: Maximum number of occurrences to process.

    Returns:
        Execution summary with total counts and per-payment details.
    """
    return await executor.execute_due_payments(
        as_of_date=as_of_date,
        max_occurrences=max_occurrences,
    )
