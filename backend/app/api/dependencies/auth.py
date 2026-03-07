"""Shared auth dependencies for API routes."""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status

from app.schemas.auth import UserOut
from app.services.auth_service import AuthService


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
    """Get current user from access token cookie or Authorization header.

    Args:
        request: FastAPI request for accessing headers and cookies.
        service: Auth service dependency.

    Returns:
        Current user schema.

    Raises:
        HTTPException: If authentication is invalid.
    """
    auth_header = request.headers.get("Authorization")
    access_token = None

    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header[7:]
    else:
        access_token = request.cookies.get("access_token")
        if access_token and access_token.startswith("Bearer "):
            access_token = access_token[7:]

    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return await service.get_current_user(access_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


__all__ = ["get_auth_service", "get_current_user"]
