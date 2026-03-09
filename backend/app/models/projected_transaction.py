"""Projected transaction model for forecast layer between planned payments and transactions."""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.planned_payment import PlannedPayment
from app.models.types import MONEY_TYPE, Money, ProjectedTransactionStatus, ProjectedTransactionType
from app.models.transaction import Transaction


class ProjectedTransaction(Base):
    """Projected transaction model for the forecast layer.

    A projected transaction represents a snapshot of one expected occurrence of a
    planned payment. It can be edited, confirmed, or skipped by the user before
    any money actually moves.

    The model has two sets of fields:
    - origin_* fields: Write-once snapshots capturing what the template said at generation time
    - projected_* fields: User's current expectation, editable while PENDING

    After CONFIRMED, the source of truth is the linked Transaction, not projected_*.

    Status transitions:
    - PENDING → CONFIRMED: Creates actual Transaction atomically
    - PENDING → SKIPPED: Skips the occurrence, no transaction created
    """

    __tablename__ = "projected_transactions"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    planned_payment_id: Mapped[UUID] = mapped_column(
        ForeignKey("planned_payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Snapshot of template at generation time (write-once)
    origin_date: Mapped[date] = mapped_column(
        nullable=False,
        index=True,
    )
    origin_amount: Mapped[Money] = mapped_column(
        MONEY_TYPE,
        nullable=False,
    )
    origin_description: Mapped[str | None] = mapped_column(
        nullable=True,
        default=None,
    )
    origin_category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Type of transaction (INCOME/EXPENSE)
    type: Mapped[ProjectedTransactionType] = mapped_column(
        nullable=False,
        index=True,
    )

    # Editable projected values (user can update while PENDING)
    projected_date: Mapped[date] = mapped_column(
        nullable=False,
        index=True,
    )
    projected_amount: Mapped[Money] = mapped_column(
        MONEY_TYPE,
        nullable=False,
    )
    projected_description: Mapped[str | None] = mapped_column(
        nullable=True,
        default=None,
    )
    projected_category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Lifecycle status
    status: Mapped[ProjectedTransactionStatus] = mapped_column(
        nullable=False,
        default=ProjectedTransactionStatus.PENDING,
        index=True,
    )

    # Link to created actual transaction
    transaction_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # When the projection was resolved (CONFIRMED or SKIPPED)
    resolved_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        default=None,
    )

    # Optimistic locking
    version: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
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

    # Relationships
    planned_payment: Mapped[PlannedPayment] = relationship(
        back_populates="projected_transactions",
    )
    transaction: Mapped[Transaction | None] = relationship(
        back_populates="projected_transaction",
    )

    # Prevent duplicate projections for same planned payment on same date
    __table_args__ = (
        UniqueConstraint(
            "planned_payment_id",
            "origin_date",
            name="uq_planned_payment_origin_date",
        ),
    )
