"""Transaction API routes."""

from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.schemas.auth import UserOut
from app.schemas.parse_create import (
    ParseAndCreateResponse,
    ParseErrorResponse,
    ParseRequest,
)
from app.services.auth_service import AuthService
from app.services.parse_create_service import TransactionParseCreateService

router = APIRouter(prefix="/transactions", tags=["transactions"])


async def get_auth_service() -> AsyncGenerator[AuthService, None]:
    """Get auth service with database session.

    Yields:
        AuthService instance.
    """
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            yield AuthService(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> UserOut:
    """Get current user from Authorization header.

    Args:
        request: FastAPI request.
        service: Auth service dependency.

    Returns:
        Current user schema.

    Raises:
        HTTPException: If authentication is invalid.
    """
    # Get token from Authorization header (Bearer token)
    auth_header = request.headers.get("Authorization")
    access_token = None

    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header[7:]

    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return await service.get_current_user(access_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


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
        request: ParseRequest with free-form text.
        current_user: Authenticated user.
        service: Parse-create service dependency.

    Returns:
        ParseAndCreateResponse with created transaction details.

    Raises:
        HTTPException 400: If amount cannot be extracted.
        HTTPException 401: If not authenticated.
    """
    try:
        return await service.parse_and_create(
            text=request.text,
            user_id=current_user.id,
            account_id=current_user.id,  # Use user_id as account_id for now
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


__all__ = ["router"]
