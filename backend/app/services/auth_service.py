"""Authentication service for user management."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    decode_token,
    generate_api_token,
    hash_api_token,
    hash_password,
    verify_password,
)
from app.repositories.api_token_repository import ApiTokenRepository
from app.repositories.refresh_session_repository import RefreshSessionRepository
from app.repositories.user_repository import UserRepository
from app.repositories.telegram_chat_link_repository import TelegramChatLinkRepository
from app.schemas.auth import ApiTokenCreate, ApiTokenOut, TelegramChatLinkOut, UserCreate, UserOut


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
        self.refresh_session_repo = RefreshSessionRepository(session)
        self.telegram_link_repo = TelegramChatLinkRepository(session)

    async def register(self, user_data: UserCreate) -> UserOut:
        """Register a new user.

        Args:
            user_data: The registration data (email, password).

        Returns:
            The created user schema.

        Raises:
            ValueError: If email is already registered.
        """
        existing = await self.user_repo.get_by_email(user_data.email)
        if existing is not None:
            raise ValueError("Email already registered")

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
        refresh_token_hash = hash_password(refresh_token)
        await self.refresh_session_repo.create(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.jwt_refresh_token_expire_days),
        )

        return access_token, refresh_token

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        """Refresh authentication tokens.

        Args:
            refresh_token: The current refresh token.

        Returns:
            A tuple of (new_access_token, new_refresh_token).

        Raises:
            ValueError: If the refresh token is invalid or revoked.
        """
        session = await self.refresh_session_repo.get_by_token(refresh_token)
        if session is None:
            raise ValueError("Invalid refresh token")

        await self.refresh_session_repo.revoke(session)

        user = await self.user_repo.get_by_id(session.user_id)
        if user is None:
            raise ValueError("User not found")

        new_access_token = self._create_access_token(user.id)
        new_refresh_token = self._create_refresh_token(user.id)
        new_refresh_token_hash = hash_password(new_refresh_token)

        await self.refresh_session_repo.create(
            user_id=user.id,
            token_hash=new_refresh_token_hash,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.jwt_refresh_token_expire_days),
        )

        return new_access_token, new_refresh_token

    async def logout(self, refresh_token: str | None = None) -> None:
        """Logout a user and invalidate the refresh token.

        Args:
            refresh_token: The current refresh token to invalidate.
        """
        if refresh_token is None:
            return

        session = await self.refresh_session_repo.get_by_token(refresh_token)
        if session is not None:
            await self.refresh_session_repo.revoke(session)

    async def get_current_user(self, access_token: str) -> UserOut:
        """Get the current user from an access token.

        Args:
            access_token: The JWT access token.

        Returns:
            The current user schema.

        Raises:
            ValueError: If the token is invalid or user not found.
        """
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
        raw_token = generate_api_token()
        token_hash = hash_api_token(raw_token)

        expires_at = datetime.now(timezone.utc) + timedelta(days=365)

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

    async def revoke_api_token(self, user_id: UUID, token_id: UUID) -> ApiTokenOut:
        """Revoke one of the user's API tokens."""
        token = await self.api_token_repo.get_by_id_for_user(token_id, user_id)
        if token is None:
            raise ValueError("API token not found")
        await self.api_token_repo.revoke(token)
        return ApiTokenOut.model_validate(token)

    async def list_telegram_links(self, user_id: UUID) -> list[TelegramChatLinkOut]:
        """List Telegram chat links for the user."""
        links = await self.telegram_link_repo.list_by_user(user_id)
        return [TelegramChatLinkOut.model_validate(link) for link in links]

    async def disconnect_telegram_link(self, user_id: UUID, link_id: UUID) -> TelegramChatLinkOut:
        """Disconnect a Telegram chat link owned by the user."""
        link = await self.telegram_link_repo.get_by_id_for_user(link_id, user_id)
        if link is None:
            raise ValueError("Telegram chat link not found")
        await self.telegram_link_repo.deactivate(link)
        return TelegramChatLinkOut.model_validate(link)

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
