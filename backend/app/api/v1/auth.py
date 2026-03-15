"""Authentication API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.dependencies.auth import get_auth_service, get_current_user
from app.core.auth_cookies import (
    clear_auth_cookies,
    set_access_cookie,
    set_refresh_cookie,
)
from app.core.config import settings
from app.core.rate_limit import build_rate_limit_key, rate_limiter
from app.schemas.auth import (
    ApiTokenCreate,
    ApiTokenOut,
    ApiTokenOutWithToken,
    LoginRequest,
    TelegramChatLinkOut,
    TelegramChatLinkUpdate,
    Token,
    TokenRefresh,
    UserCreate,
    UserOut,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


def enforce_auth_rate_limit(request: Request) -> None:
    """Rate-limit unauthenticated auth endpoints per client IP."""
    rate_limiter.check(
        build_rate_limit_key(request, "auth"),
        limit=settings.auth_rate_limit_requests,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: UserCreate,
    service: AuthService = Depends(get_auth_service),
    _: None = Depends(enforce_auth_rate_limit),
) -> UserOut:
    """Register a new user.

    Args:
        user_data: Registration data (email, password).
        service: Auth service dependency.

    Returns:
        Created user schema.

    Raises:
        HTTPException: If email is already registered.
    """
    try:
        user = await service.register(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    service: AuthService = Depends(get_auth_service),
    _: None = Depends(enforce_auth_rate_limit),
) -> Token:
    """Authenticate a user and set cookies.

    Args:
        response: FastAPI response for cookie setting.
        login_data: Login credentials (email, password).
        service: Auth service dependency.

    Returns:
        Token response with access token.

    Raises:
        HTTPException: If credentials are invalid.
    """
    try:
        access_token, refresh_token = await service.login(
            login_data.email,
            login_data.password,
        )
        set_access_cookie(response, access_token)
        set_refresh_cookie(response, refresh_token)
        return Token(access_token=access_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


@router.post("/refresh", response_model=TokenRefresh)
async def refresh(
    response: Response,
    request: Request,
    service: AuthService = Depends(get_auth_service),
    _: None = Depends(enforce_auth_rate_limit),
) -> TokenRefresh:
    """Refresh authentication tokens.

    Args:
        response: FastAPI response for cookie setting.
        request: FastAPI request for accessing refresh token cookie.
        service: Auth service dependency.

    Returns:
        Token refresh response with new tokens.

    Raises:
        HTTPException: If refresh token is invalid.
    """
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        new_access, new_refresh = await service.refresh_tokens(refresh_token)
        set_access_cookie(response, new_access)
        set_refresh_cookie(response, new_refresh)
        return TokenRefresh(access_token=new_access, refresh_token=new_refresh)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Logout a user and invalidate the refresh token.

    Args:
        response: FastAPI response for cookie clearing.
        request: FastAPI request for accessing refresh token cookie.
        service: Auth service dependency.

    Returns:
        Logout confirmation.
    """
    refresh_token = request.cookies.get("refresh_token")
    await service.logout(refresh_token)
    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
async def get_me(
    user: UserOut = Depends(get_current_user),
) -> UserOut:
    """Get current user profile.

    Args:
        user: Current user from access token.

    Returns:
        Current user schema.
    """
    return user


@router.post("/api-tokens", response_model=ApiTokenOutWithToken)
async def create_api_token(
    token_data: ApiTokenCreate,
    user: UserOut = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> ApiTokenOutWithToken:
    """Create a new API token.

    Args:
        token_data: Token creation data (name).
        user: Current user from access token.
        service: Auth service dependency.

    Returns:
        Created API token with raw token shown once.
        The raw token should be stored securely by the user.
    """
    api_token, raw_token = await service.create_api_token(user.id, token_data)
    token_out = api_token.model_dump()
    token_out["raw_token"] = raw_token
    return ApiTokenOutWithToken(**token_out)


@router.get("/api-tokens", response_model=list[ApiTokenOut])
async def list_api_tokens(
    user: UserOut = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> list[ApiTokenOut]:
    """List active API tokens for current user.

    Args:
        user: Current user from access token.
        service: Auth service dependency.

    Returns:
        List of active API tokens.
    """
    return await service.list_api_tokens(user.id)


@router.delete("/api-tokens/{token_id}", response_model=ApiTokenOut)
async def revoke_api_token(
    token_id: UUID,
    user: UserOut = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> ApiTokenOut:
    """Revoke one API token owned by the current user."""
    try:
        return await service.revoke_api_token(user.id, token_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get("/telegram-links", response_model=list[TelegramChatLinkOut])
async def list_telegram_links(
    user: UserOut = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> list[TelegramChatLinkOut]:
    """List Telegram chat links for the current user."""
    return await service.list_telegram_links(user.id)


@router.delete("/telegram-links/{link_id}", response_model=TelegramChatLinkOut)
async def disconnect_telegram_link(
    link_id: UUID,
    user: UserOut = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> TelegramChatLinkOut:
    """Disconnect one Telegram chat link owned by the current user."""
    try:
        return await service.disconnect_telegram_link(user.id, link_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.patch("/telegram-links/{link_id}", response_model=TelegramChatLinkOut)
async def update_telegram_link(
    link_id: UUID,
    payload: TelegramChatLinkUpdate,
    user: UserOut = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> TelegramChatLinkOut:
    """Update the default account for one Telegram chat link."""
    try:
        return await service.update_telegram_link_account(
            user.id,
            link_id,
            payload.account_id,
        )
    except ValueError as e:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if str(e) in {"Telegram chat link not found", "Account not found"}
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=status_code,
            detail=str(e),
        ) from e
