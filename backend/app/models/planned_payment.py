"""Planned payment model for recurring transaction generation."""

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.types import MONEY_TYPE, Money, Recurrence

if TYPE_CHECKING:
    from app.models.projected_transaction import ProjectedTransaction
    from app.models.transaction import Transaction


class PlannedPayment(Base):
    """Planned payment model for recurring financial obligations.

    Planned payments are scheduled transactions that can be automatically
    generated on a recurring basis. Common use cases include:
    - Rent payments
    - Subscription fees
    - Utility bills
    - Loan repayments

    Each planned payment belongs to a user and references:
    - account_id: Which account the transactions affect
    - category_id: How to categorize generated transactions (optional)
    - amount: Fixed amount for each occurrence

    The recurrence rule defines how often transactions are generated.
    The active flag allows pausing generation without deleting the plan.

    Generated transactions reference their source planned payment via
    the planned_occurrence_id to enable idempotent generation and
    tracking of recurring obligations.
    """

    __tablename__ = "planned_payments"

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
    # Account that this planned payment affects
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Category for classification (optional)
    category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Fixed amount for each occurrence
    amount: Mapped[Money] = mapped_column(
        MONEY_TYPE,
        nullable=False,
    )
    # Description/title for human readability
    description: Mapped[str | None] = mapped_column(
        nullable=True,
        default=None,
    )
    # Recurrence pattern for generating occurrences
    recurrence: Mapped[Recurrence] = mapped_column(
        nullable=False,
        index=True,
    )
    # Start date for the planned payment
    start_date: Mapped[date] = mapped_column(
        nullable=False,
        index=True,
    )
    # Optional end date (if None, continues indefinitely until deactivated)
    end_date: Mapped[date | None] = mapped_column(
        nullable=True,
        default=None,
        index=True,
    )
    # Next date when a transaction should be generated
    next_due_at: Mapped[date] = mapped_column(
        nullable=False,
        index=True,
    )
    # Whether this planned payment is active
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        index=True,
    )
    # Generated transactions for this planned payment
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="planned_payment",
        cascade="all, delete-orphan",
    )
    # Projected transactions for this planned payment
    projected_transactions: Mapped[list["ProjectedTransaction"]] = relationship(
        back_populates="planned_payment",
        cascade="all, delete-orphan",
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
