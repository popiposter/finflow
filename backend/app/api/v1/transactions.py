"""Transaction API routes."""

from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import get_current_user
from app.schemas.auth import UserOut
from app.schemas.parse_create import (
    ParseAndCreateResponse,
    ParseErrorResponse,
    ParseRequest,
)
from app.services.parse_create_service import TransactionParseCreateService

router = APIRouter(prefix="/transactions", tags=["transactions"])


async def get_parse_create_service() -> AsyncGenerator[
    TransactionParseCreateService, None
]:
    """Get parse-create service with database session.

    Yields:
        TransactionParseCreateService instance.
    """
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            yield TransactionParseCreateService(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@router.post(
    "/parse-and-create",
    response_model=ParseAndCreateResponse,
    responses={
        400: {"model": ParseErrorResponse, "description": "Invalid request"},
        401: {"description": "Not authenticated"},
    },
)
async def parse_and_create(
    request: ParseRequest,
    current_user: UserOut = Depends(get_current_user),
    service: TransactionParseCreateService = Depends(get_parse_create_service),
) -> ParseAndCreateResponse:
    """Parse free-form text and create a transaction.

    Accepts free-form text from iOS Shortcut and creates a transaction
    in the database.

    Args:
        request: ParseRequest with free-form text and target account.
        current_user: Authenticated user.
        service: Parse-create service dependency.

    Returns:
        ParseAndCreateResponse with created transaction details.

    Raises:
        HTTPException 400: If amount cannot be extracted or account is missing.
        HTTPException 401: If not authenticated.
    """
    if request.account_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="account_id is required until default account selection is implemented",
        )

    try:
        return await service.parse_and_create(
            text=request.text,
            user_id=current_user.id,
            account_id=request.account_id,
            category_id=request.category_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


__all__ = ["router"]
