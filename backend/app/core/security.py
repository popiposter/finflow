"""Security helpers for password hashing and JWT."""

import secrets
from datetime import datetime, timedelta, timezone

import pwdlib
from jwt import decode as jwt_decode
from jwt import encode as jwt_encode

from app.core.config import settings

# Password hashing using pwdlib recommended hasher
_password_hasher = pwdlib.PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a password using the recommended hasher.

    Args:
        password: The plain-text password to hash.

    Returns:
        The hashed password string.
    """
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash.

    Args:
        password: The plain-text password to verify.
        password_hash: The stored password hash.

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        return _password_hasher.verify(password, password_hash)
    except Exception:
        return False


def create_access_token(subject: str) -> str:
    """Create a JWT access token.

    Args:
        subject: The subject (user ID) for the token.

    Returns:
        The encoded JWT token string.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": "access",
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
        "iat": now,
    }
    return jwt_encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def create_refresh_token(subject: str) -> str:
    """Create a JWT refresh token.

    Args:
        subject: The subject (user ID) for the token.

    Returns:
        The encoded JWT token string.
    """
    import secrets

    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": "refresh",
        "exp": now + timedelta(days=settings.jwt_refresh_token_expire_days),
        "iat": now,
        # Add a unique nonce to ensure each token is unique even within same second
        "jti": secrets.token_hex(8),
    }
    return jwt_encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token string.

    Returns:
        The decoded token payload.

    Raises:
        InvalidTokenError: If the token is invalid or expired.
    """
    return jwt_decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def generate_api_token() -> str:
    """Generate a random API token.

    Returns:
        The raw token string that should be shown once to the user.
    """
    return secrets.token_urlsafe(settings.api_token_length)


def hash_api_token(token: str) -> str:
    """Hash an API token for storage.

    Args:
        token: The raw API token to hash.

    Returns:
        The hashed token for database storage.
    """
    return _password_hasher.hash(token)


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "generate_api_token",
    "hash_api_token",
]
