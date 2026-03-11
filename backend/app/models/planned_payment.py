"""Planned payment model for recurring template defaults."""

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


class PlannedPayment(Base):
    """Planned payment model for recurring financial templates.

    Planned payments are reusable templates for forecast-first cashflow.
    Common use cases include:
    - Rent payments
    - Subscription fees
    - Utility bills
    - Loan repayments

    Each planned payment belongs to a user and stores defaults for future
    projected occurrences:
    - account_id: Which account future projections affect
    - category_id: Default classification for generated projections (optional)
    - amount: Default amount for each occurrence

    The recurrence rule defines how often a new projected transaction is
    generated. The active flag allows pausing the template without deleting it.
    Actual transactions may still retain planned_payment_id as audit metadata,
    but templates generate projections first.
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
    # Next date when a projected occurrence should be generated
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
    # Generated projected occurrences for this template
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
