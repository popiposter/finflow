"""Projected transaction API routes."""

from datetime import date, datetime
from decimal import Decimal
from typing import AsyncGenerator

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import UUID4

from app.api.dependencies.auth import get_current_user
from app.exceptions import (
    AccountNotFoundError,
    CategoryNotFoundError,
    InvalidProjectionStatusError,
    ProjectionNotFoundError,
)
from app.models.projected_transaction import ProjectedTransaction
from app.models.types import ProjectedTransactionStatus
from app.repositories.projected_transaction_repository import ProjectedTransactionRepository
from app.schemas.auth import UserOut
from app.schemas.finance import (
    ProjectedTransactionConfirmRequest,
    ProjectedTransactionConfirmResponse,
    ProjectedTransactionOut,
    ProjectedTransactionUpdate,
)
from app.services.projected_transaction_service import ProjectedTransactionService

router = APIRouter(prefix="/projected-transactions", tags=["projected-transactions"])


async def get_repo(
    current_user: UserOut = Depends(get_current_user),
) -> AsyncGenerator[ProjectedTransactionRepository, None]:
    """Get projected transaction repository with database session.

    Args:
        current_user: Current authenticated user.

    Yields:
        ProjectedTransactionRepository instance.
    """
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            yield ProjectedTransactionRepository(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_service(
    current_user: UserOut = Depends(get_current_user),
) -> AsyncGenerator[ProjectedTransactionService, None]:
    """Get projected transaction service with database session.

    Args:
        current_user: Current authenticated user.

    Yields:
        ProjectedTransactionService instance.
    """
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            yield ProjectedTransactionService(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@router.get(
    "",
    response_model=list[ProjectedTransactionOut],
)
async def list_projected_transactions(
    status: ProjectedTransactionStatus | None = None,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    current_user: UserOut = Depends(get_current_user),
    service: ProjectedTransactionService = Depends(get_service),
) -> list[ProjectedTransactionOut]:
    """List projected transactions for the current user.

    Args:
        status: Filter by status (optional).
        from_date: Filter by from date (optional).
        to_date: Filter by to date (optional).
        current_user: Authenticated user.
        service: Projected transaction service dependency.

    Returns:
        List of projected transactions matching the filters.
    """
    projections = await service.list_projections(
        user_id=current_user.id,
        status=status,
        from_date=from_date,
        to_date=to_date,
    )
    return [ProjectedTransactionOut.model_validate(p) for p in projections]


@router.get(
    "/{projected_transaction_id}",
    response_model=ProjectedTransactionOut,
)
async def get_projected_transaction(
    projected_transaction_id: str,
    current_user: UserOut = Depends(get_current_user),
    service: ProjectedTransactionService = Depends(get_service),
) -> ProjectedTransactionOut:
    """Get a specific projected transaction by ID.

    Args:
        projected_transaction_id: The projected transaction's UUID (as string).
        current_user: Authenticated user.
        service: Projected transaction service dependency.

    Returns:
        The projected transaction.

    Raises:
        HTTPException 404: If projected transaction not found or not owned by user.
    """
    from uuid import UUID

    projection_id = UUID(projected_transaction_id)
    projection = await service.get_projection(
        user_id=current_user.id,
        projected_transaction_id=projection_id,
    )

    if projection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projected transaction not found",
        )

    return ProjectedTransactionOut.model_validate(projection)


@router.patch(
    "/{projected_transaction_id}",
    response_model=ProjectedTransactionOut,
)
async def update_projected_transaction(
    projected_transaction_id: str,
    update_data: ProjectedTransactionUpdate,
    current_user: UserOut = Depends(get_current_user),
    service: ProjectedTransactionService = Depends(get_service),
) -> ProjectedTransactionOut:
    """Update a pending projected transaction.

    Args:
        projected_transaction_id: The projected transaction's UUID (as string).
        update_data: The fields to update.
        current_user: Authenticated user.
        service: Projected transaction service dependency.

    Returns:
        The updated projected transaction.

    Raises:
        HTTPException 404: If projected transaction not found or not owned by user.
        HTTPException 409: If status != PENDING.
    """
    from uuid import UUID

    projection_id = UUID(projected_transaction_id)

    try:
        updated = await service.update_projection(
            user_id=current_user.id,
            projected_transaction_id=projection_id,
            projected_amount=update_data.projected_amount,
            projected_date=update_data.projected_date,
            projected_description=update_data.projected_description,
            projected_category_id=update_data.projected_category_id,
        )
        return ProjectedTransactionOut.model_validate(updated)
    except ProjectionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projected transaction not found",
        ) from e
    except CategoryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        ) from e
    except InvalidProjectionStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


@router.post(
    "/{projected_transaction_id}/confirm",
    response_model=ProjectedTransactionConfirmResponse,
)
async def confirm_projected_transaction(
    projected_transaction_id: str,
    confirm_data: ProjectedTransactionConfirmRequest = Body(default=None),
    current_user: UserOut = Depends(get_current_user),
    service: ProjectedTransactionService = Depends(get_service),
) -> ProjectedTransactionConfirmResponse:
    """Confirm a projected transaction, creating an actual transaction.

    Args:
        projected_transaction_id: The projected transaction's UUID (as string).
        confirm_data: Optional override values for confirmation.
        current_user: Authenticated user.
        service: Projected transaction service dependency.

    Returns:
        The updated projected transaction and created transaction ID.

    Raises:
        HTTPException 404: If projected transaction not found or not owned by user.
        HTTPException 409: If status != PENDING.
    """
    from uuid import UUID

    projection_id = UUID(projected_transaction_id)

    try:
        updated, transaction_id = await service.confirm_projection(
            user_id=current_user.id,
            projected_transaction_id=projection_id,
            amount=confirm_data.amount if confirm_data else None,
            date_=confirm_data.date if confirm_data and confirm_data.date else None,
            description=confirm_data.description if confirm_data else None,
            category_id=confirm_data.category_id if confirm_data else None,
        )
        return ProjectedTransactionConfirmResponse(
            projected_transaction=ProjectedTransactionOut.model_validate(updated),
            transaction_id=transaction_id,
        )
    except ProjectionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projected transaction not found",
        ) from e
    except CategoryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        ) from e
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        ) from e
    except InvalidProjectionStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


@router.post(
    "/{projected_transaction_id}/skip",
    response_model=ProjectedTransactionOut,
)
async def skip_projected_transaction(
    projected_transaction_id: str,
    current_user: UserOut = Depends(get_current_user),
    service: ProjectedTransactionService = Depends(get_service),
) -> ProjectedTransactionOut:
    """Skip a projected transaction.

    Args:
        projected_transaction_id: The projected transaction's UUID (as string).
        current_user: Authenticated user.
        service: Projected transaction service dependency.

    Returns:
        The updated projected transaction (status = SKIPPED).

    Raises:
        HTTPException 404: If projected transaction not found or not owned by user.
        HTTPException 409: If status != PENDING.
    """
    from uuid import UUID

    projection_id = UUID(projected_transaction_id)

    try:
        updated = await service.skip_projection(
            user_id=current_user.id,
            projected_transaction_id=projection_id,
        )
        return ProjectedTransactionOut.model_validate(updated)
    except ProjectionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projected transaction not found",
        ) from e
    except InvalidProjectionStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


__all__ = ["router"]
