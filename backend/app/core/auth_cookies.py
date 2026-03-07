"""Authentication cookie helpers for web auth."""

from fastapi import Response

from app.core.config import settings


def get_cookie_domain() -> str | None:
    """Get the cookie domain for secure cookies.

    Returns:
        The domain to use, or None for default (current host only).
    """
    return None  # Default to current host only


def get_secure_flag() -> bool:
    """Determine if cookies should be marked as Secure.

    Returns:
        True if running in production, False otherwise.
    """
    # Don't use Secure flag in tests (pytest) to allow HTTP cookie testing
    import os

    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return settings.is_production


def set_access_cookie(response: Response, token: str) -> None:
    """Set the access token in a cookie on the response.

    Args:
        response: The FastAPI response object to set the cookie on.
        token: The JWT access token to store.
    """
    cookie_domain = get_cookie_domain()
    secure_flag = get_secure_flag()

    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        samesite="lax",
        secure=secure_flag,
        domain=cookie_domain,
        max_age=settings.jwt_access_token_expire_minutes * 60,
    )


def set_refresh_cookie(response: Response, token: str) -> None:
    """Set the refresh token in a cookie on the response.

    Args:
        response: The FastAPI response object to set the cookie on.
        token: The JWT refresh token to store.
    """
    cookie_domain = get_cookie_domain()
    secure_flag = get_secure_flag()

    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=secure_flag,
        domain=cookie_domain,
        max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
    )


def clear_access_cookie(response: Response) -> None:
    """Clear the access token cookie on the response.

    Args:
        response: The FastAPI response object to clear the cookie from.
    """
    cookie_domain = get_cookie_domain()
    secure_flag = get_secure_flag()

    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=secure_flag,
        domain=cookie_domain,
    )


def clear_refresh_cookie(response: Response) -> None:
    """Clear the refresh token cookie on the response.

    Args:
        response: The FastAPI response object to clear the cookie from.
    """
    cookie_domain = get_cookie_domain()
    secure_flag = get_secure_flag()

    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        samesite="lax",
        secure=secure_flag,
        domain=cookie_domain,
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear both auth cookies on the response.

    Args:
        response: The FastAPI response object to clear cookies from.
    """
    clear_access_cookie(response)
    clear_refresh_cookie(response)
