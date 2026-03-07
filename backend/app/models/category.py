"""Category model for organizing transactions hierarchically."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.types import CategoryType


class Category(Base):
    """Category model for organizing transactions hierarchically.

    Categories support nesting via parent_id to create a tree structure.
    Top-level categories have parent_id = NULL.

    User ownership determines scope:
    - user_id set: Private category for that user
    - user_id NULL: System-level category (shared across all users)

    Note: System category seed migration is not implemented in Stage 1.

    Examples:
        Income
            ├── Salary
            └── Investment Returns
        Expense
            ├── Housing
            │   ├── Rent
            │   └── Utilities
            └── Food
                ├── Groceries
                └── Restaurants

    Each category is typed as either INCOME or EXPENSE.
    """

    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    # NULL user_id means system-level (shared) category
    name: Mapped[str] = mapped_column(
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        nullable=True,
        default=None,
    )
    type: Mapped[CategoryType] = mapped_column(
        nullable=False,
        index=True,
    )
    # For hierarchical categories
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Active categories are included in reports; inactive are archived
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        index=True,
    )
    # Display order within parent (for UI sorting)
    display_order: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
