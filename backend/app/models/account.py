"""Account model for tracking financial accounts."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.types import MONEY_TYPE, AccountType, Money


class Account(Base):
    """Account model for tracking financial accounts.

    Accounts can be any financial instrument that holds value:
    - Checking/savings accounts
    - Credit cards
    - Cash wallets
    - Investment accounts
    - Loans

    Each account belongs to a user and tracks a current balance.
    Account types determine the kind of account and its behavior.
    """

    __tablename__ = "accounts"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        nullable=False,
        index=True,
    )
    type: Mapped[AccountType] = mapped_column(
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        nullable=True,
        default=None,
    )
    # Current balance as of last reconciliation
    # Positive for asset accounts, negative for liability accounts
    current_balance: Mapped[Money] = mapped_column(
        MONEY_TYPE,
        nullable=False,
        default=Decimal("0.00"),
    )
    # Original currency code (e.g., "USD", "EUR") - for multi-currency support
    currency_code: Mapped[str] = mapped_column(
        nullable=False,
        default="USD",
        index=True,
    )
    # Active accounts are included in reports; inactive are archived
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        index=True,
    )
    # When the account was opened
    opened_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        default=None,
    )
    # When the account was closed (if applicable)
    closed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        default=None,
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
