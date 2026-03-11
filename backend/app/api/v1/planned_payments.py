"""Planned payment API routes."""

from datetime import date
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import get_current_user
from app.repositories.planned_payment_repository import PlannedPaymentRepository
from app.schemas.auth import UserOut
from app.schemas.finance import (
    PlannedPaymentCreate,
    PlannedPaymentOut,
    ProjectionGenerationResult,
)
from app.services.projection_scheduler_service import ProjectionSchedulerService

router = APIRouter(prefix="/planned-payments", tags=["planned-payments"])


async def get_repo(
    current_user: UserOut = Depends(get_current_user),
) -> AsyncGenerator[PlannedPaymentRepository, None]:
    """Get planned payment repository with database session.

    Args:
        current_user: Current authenticated user.

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


async def get_generation_service() -> AsyncGenerator[ProjectionSchedulerService, None]:
    """Get projection generation service with database session.

    Yields:
        ProjectionSchedulerService instance.
    """
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            yield ProjectionSchedulerService(session)
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
    repo: PlannedPaymentRepository = Depends(get_repo),
) -> PlannedPaymentOut:
    """Create a new planned-payment template.

    Args:
        payment_data: Planned payment creation data.
        current_user: Authenticated user.
        repo: Planned payment repository dependency.

    Returns:
        Created planned-payment template.
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
    repo: PlannedPaymentRepository = Depends(get_repo),
) -> list[PlannedPaymentOut]:
    """List all active planned-payment templates for the current user.

    Args:
        current_user: Authenticated user.
        repo: Planned payment repository dependency.

    Returns:
        List of active planned-payment templates owned by the user.
    """
    payments = await repo.get_active_by_user(current_user.id)
    return [PlannedPaymentOut.model_validate(p) for p in payments]


@router.get(
    "/{planned_payment_id}",
    response_model=PlannedPaymentOut,
)
async def get_planned_payment(
    planned_payment_id: str,
    current_user: UserOut = Depends(get_current_user),
    repo: PlannedPaymentRepository = Depends(get_repo),
) -> PlannedPaymentOut:
    """Get a specific planned-payment template by ID.

    Args:
        planned_payment_id: The planned payment's UUID (as string).
        current_user: Authenticated user.
        repo: Planned payment repository dependency.

    Returns:
        The planned-payment template.

    Raises:
        HTTPException 404: If planned payment not found or not owned by user.
    """
    from uuid import UUID

    payment_id = UUID(planned_payment_id)
    payment = await repo.get_by_id(payment_id)

    if payment is None or payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planned payment not found",
        )

    return PlannedPaymentOut.model_validate(payment)


@router.put(
    "/{planned_payment_id}",
    response_model=PlannedPaymentOut,
)
async def update_planned_payment(
    planned_payment_id: str,
    payment_data: PlannedPaymentCreate,
    current_user: UserOut = Depends(get_current_user),
    repo: PlannedPaymentRepository = Depends(get_repo),
) -> PlannedPaymentOut:
    """Update a planned-payment template.

    Args:
        planned_payment_id: The planned payment's UUID (as string).
        payment_data: Planned payment update data.
        current_user: Authenticated user.
        repo: Planned payment repository dependency.

    Returns:
        Updated planned-payment template.

    Raises:
        HTTPException 404: If planned payment not found or not owned by user.
    """
    from uuid import UUID

    payment_id = UUID(planned_payment_id)
    payment = await repo.get_by_id(payment_id)

    if payment is None or payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planned payment not found",
        )

    payment.account_id = payment_data.account_id
    payment.amount = payment_data.amount
    payment.recurrence = payment_data.recurrence
    payment.start_date = payment_data.start_date
    payment.next_due_at = payment_data.next_due_at or payment_data.start_date
    payment.category_id = payment_data.category_id
    payment.description = payment_data.description
    payment.end_date = payment_data.end_date
    payment.is_active = payment_data.is_active

    updated = await repo.update(payment)
    return PlannedPaymentOut.model_validate(updated)


@router.delete(
    "/{planned_payment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_planned_payment(
    planned_payment_id: str,
    current_user: UserOut = Depends(get_current_user),
    repo: PlannedPaymentRepository = Depends(get_repo),
) -> None:
    """Soft-delete a planned-payment template by deactivating it.

    Args:
        planned_payment_id: The planned payment's UUID (as string).
        current_user: Authenticated user.
        repo: Planned payment repository dependency.

    Raises:
        HTTPException 404: If planned payment not found or not owned by user.
    """
    from uuid import UUID

    payment_id = UUID(planned_payment_id)
    payment = await repo.get_by_id(payment_id)

    if payment is None or payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planned payment not found",
        )

    await repo.deactivate(payment)


@router.post(
    "/generate",
    response_model=list[ProjectionGenerationResult],
)
async def generate_transactions(
    current_user: UserOut = Depends(get_current_user),
    service: ProjectionSchedulerService = Depends(get_generation_service),
    as_of_date: date | None = None,
) -> list[ProjectionGenerationResult]:
    """Generate due projections for the current user's planned payments.

    Args:
        current_user: Authenticated user.
        service: Planned payment generation service dependency.
        as_of_date: Optional date to generate up to. Defaults to today.

    Returns:
        Projection generation results for each processed planned payment.
    """
    results = await service.generate_due_projections(
        user_id=current_user.id,
        as_of_date=as_of_date,
    )
    return results


__all__ = ["router"]
