"""Refresh session repository for database access."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.refresh_session import RefreshSession


class RefreshSessionRepository:
    """Repository for refresh session database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.session = session

    async def create(
        self,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshSession:
        """Create a new refresh session.

        Args:
            user_id: The user's UUID.
            token_hash: The hashed refresh token.
            expires_at: When the session expires.

        Returns:
            The created refresh session.
        """
        session = RefreshSession(
            user_id=user_id,
            refresh_token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(session)
        await self.session.flush()
        return session

    async def get_by_token(self, token: str) -> RefreshSession | None:
        """Get a refresh session by verifying the token against stored hashes.

        Args:
            token: The plain-text refresh token to verify.

        Returns:
            The refresh session if found and verified, None otherwise.
        """
        stmt = select(RefreshSession).where(
            RefreshSession.revoked_at.is_(None),
            RefreshSession.expires_at > datetime.now(timezone.utc),
        )
        result = await self.session.scalars(stmt)
        sessions = list(result.all())

        for session in sessions:
            if verify_password(token, session.refresh_token_hash):
                return session
        return None

    async def get_active_by_user(
        self,
        user_id: UUID,
    ) -> list[RefreshSession]:
        """Get active (non-revoked) refresh sessions for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            List of active refresh sessions.
        """
        stmt = select(RefreshSession).where(
            RefreshSession.user_id == user_id,
            RefreshSession.revoked_at.is_(None),
            RefreshSession.expires_at > datetime.now(timezone.utc),
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def revoke(self, session: RefreshSession) -> RefreshSession:
        """Revoke a refresh session.

        Args:
            session: The refresh session to revoke.

        Returns:
            The revoked session.
        """
        session.revoked_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(session)
        return session

    async def get_latest_session(self, user_id: UUID) -> RefreshSession | None:
        """Get the most recent active refresh session for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            The most recent active refresh session, or None if none exist.
        """
        stmt = (
            select(RefreshSession)
            .where(
                RefreshSession.user_id == user_id,
                RefreshSession.revoked_at.is_(None),
                RefreshSession.expires_at > datetime.now(timezone.utc),
            )
            .order_by(RefreshSession.created_at.desc())
        )
        result = await self.session.scalar(stmt)
        return result
