"""API token model for iOS Shortcut authentication."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ApiToken(Base):
    """API token model for long-lived API access (e.g., iOS Shortcuts)."""

    __tablename__ = "api_tokens"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(nullable=False)
    token_hash: Mapped[str] = mapped_column(
        unique=True,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(default=None)
    expires_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    is_revoked: Mapped[bool] = mapped_column(default=False, nullable=False)
