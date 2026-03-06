"""Authentication service for user management."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_api_token, hash_password, verify_password
from app.repositories.api_token_repository import ApiTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import ApiTokenCreate, ApiTokenOut, UserCreate, UserOut


class AuthService:
    """Service for authentication use-cases."""

    def __init__(self, session: AsyncSession):
        """Initialize the service with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.session = session
        self.user_repo = UserRepository(session)
        self.api_token_repo = ApiTokenRepository(session)

    async def register(self, user_data: UserCreate) -> UserOut:
        """Register a new user.

        Args:
            user_data: The registration data (email, password).

        Returns:
            The created user schema.

        Raises:
            ValueError: If email is already registered.
        """
        # Check if email already exists
        existing = await self.user_repo.get_by_email(user_data.email)
        if existing is not None:
            raise ValueError("Email already registered")

        # Hash password and create user
        hashed_password = hash_password(user_data.password)
        user = await self.user_repo.create(user_data.email, hashed_password)

        return UserOut.model_validate(user)

    async def login(self, email: str, password: str) -> tuple[str, str]:
        """Authenticate a user and return tokens.

        Args:
            email: The user's email address.
            password: The user's plain-text password.

        Returns:
            A tuple of (access_token, refresh_token).

        Raises:
            ValueError: If credentials are invalid.
        """
        user = await self.user_repo.get_by_email(email)
        if user is None:
            raise ValueError("Invalid credentials")

        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")

        access_token = self._create_access_token(user.id)
        refresh_token = self._create_refresh_token(user.id)

        return access_token, refresh_token

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        """Refresh authentication tokens.

        Args:
            refresh_token: The current refresh token.

        Returns:
            A tuple of (new_access_token, new_refresh_token).

        Raises:
            ValueError: If the refresh token is invalid.
        """
        from app.core.security import decode_token

        try:
            payload = decode_token(refresh_token)
        except Exception as exc:
            raise ValueError("Invalid refresh token") from exc

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        subject = payload.get("sub")
        if subject is None:
            raise ValueError("Invalid token payload")

        user_id = UUID(subject)
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")

        new_access_token = self._create_access_token(user.id)
        new_refresh_token = self._create_refresh_token(user.id)

        return new_access_token, new_refresh_token

    async def logout(self, refresh_token: str) -> None:
        """Logout a user (invalidate the refresh token).

        Args:
            refresh_token: The current refresh token (for potential future revocation).
        """
        # Currently a no-op since JWTs are valid until expiry.
        # In production, implement token revocation list if needed.
        pass

    async def get_current_user(self, access_token: str) -> UserOut:
        """Get the current user from an access token.

        Args:
            access_token: The JWT access token.

        Returns:
            The current user schema.

        Raises:
            ValueError: If the token is invalid or user not found.
        """
        from app.core.security import decode_token

        try:
            payload = decode_token(access_token)
        except Exception as exc:
            raise ValueError("Invalid access token") from exc

        if payload.get("type") != "access":
            raise ValueError("Invalid token type")

        subject = payload.get("sub")
        if subject is None:
            raise ValueError("Invalid token payload")

        user_id = UUID(subject)
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")

        return UserOut.model_validate(user)

    async def create_api_token(
        self,
        user_id: UUID,
        token_data: ApiTokenCreate,
    ) -> tuple[ApiTokenOut, str]:
        """Create a new API token.

        Args:
            user_id: The user's UUID.
            token_data: The token creation data (name).

        Returns:
            A tuple of (api_token_schema, raw_token).
        """
        raw_token = self._generate_raw_api_token()
        token_hash = hash_api_token(raw_token)

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=365,  # Default 1 year expiry
        )

        api_token = await self.api_token_repo.create(
            user_id=user_id,
            name=token_data.name,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        return ApiTokenOut.model_validate(api_token), raw_token

    async def list_api_tokens(self, user_id: UUID) -> list[ApiTokenOut]:
        """List active API tokens for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            List of active API tokens.
        """
        tokens = await self.api_token_repo.get_active_by_user(user_id)
        return [ApiTokenOut.model_validate(token) for token in tokens]

    def _create_access_token(self, user_id: UUID) -> str:
        """Create an access token for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            The encoded JWT access token.
        """
        from app.core.security import create_access_token

        return create_access_token(str(user_id))

    def _create_refresh_token(self, user_id: UUID) -> str:
        """Create a refresh token for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            The encoded JWT refresh token.
        """
        from app.core.security import create_refresh_token

        return create_refresh_token(str(user_id))

    def _generate_raw_api_token(self) -> str:
        """Generate a raw API token.

        Returns:
            The raw token string.
        """
        from app.core.security import generate_api_token

        return generate_api_token()
