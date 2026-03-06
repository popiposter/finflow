"""Refresh session model for server-side token revocation."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RefreshSession(Base):
    """Refresh session model for tracking active refresh tokens.

    This table stores hashes of refresh tokens to enable server-side
    revocation. When a refresh token is used (via /refresh or /logout),
    it is invalidated so it cannot be reused.
    """

    __tablename__ = "refresh_sessions"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
    )
    refresh_token_hash: Mapped[str] = mapped_column(
        unique=True,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        default=None,
    )
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )
