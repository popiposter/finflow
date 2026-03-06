"""API token repository for database access."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_token import ApiToken


class ApiTokenRepository:
    """Repository for API token database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.session = session

    async def create(
        self,
        user_id: UUID,
        name: str,
        token_hash: str,
        expires_at: datetime,
    ) -> ApiToken:
        """Create a new API token.

        Args:
            user_id: The user's UUID.
            name: The token's display name.
            token_hash: The hashed token for storage.
            expires_at: When the token expires.

        Returns:
            The created API token.
        """
        token = ApiToken(
            user_id=user_id,
            name=name,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_by_hash(self, token_hash: str) -> ApiToken | None:
        """Get an API token by its hash.

        Args:
            token_hash: The hashed token.

        Returns:
            The API token if found, None otherwise.
        """
        stmt = select(ApiToken).where(ApiToken.token_hash == token_hash)
        result = await self.session.scalar(stmt)
        return result

    async def get_active_by_user(
        self,
        user_id: UUID,
        current_time: datetime | None = None,
    ) -> list[ApiToken]:
        """Get active (non-revoked, non-expired) tokens for a user.

        Args:
            user_id: The user's UUID.
            current_time: Optional current time for expiry check.

        Returns:
            List of active API tokens.
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        stmt = (
            select(ApiToken)
            .where(
                ApiToken.user_id == user_id,
                ~ApiToken.is_revoked,
                ApiToken.expires_at > current_time,
            )
            .order_by(ApiToken.created_at.desc())
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def revoke(self, token: ApiToken) -> ApiToken:
        """Revoke an API token.

        Args:
            token: The API token to revoke.

        Returns:
            The revoked token.
        """
        token.is_revoked = True
        await self.session.flush()
        return token

    async def mark_used(self, token: ApiToken, now: datetime | None = None) -> ApiToken:
        """Update the last_used_at timestamp for a token.

        Args:
            token: The API token.
            now: Optional current time.

        Returns:
            The updated token.
        """
        if now is None:
            now = datetime.now(timezone.utc)
        token.last_used_at = now
        await self.session.flush()
        return token
