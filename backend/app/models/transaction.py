"""Transaction model for financial entries."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.types import MONEY_TYPE, Money, TransactionType

if TYPE_CHECKING:
    from app.models.planned_payment import PlannedPayment
    from app.models.projected_transaction import ProjectedTransaction


class Transaction(Base):
    """Transaction model for financial entries.

    Transactions track the movement of money with two important dates:
    - date_accrual: When the transaction is recognized (for accounting)
    - date_cash: When the actual cash movement occurs

    This supports both accrual-basis and cash-basis accounting.

    Each transaction links to:
    - user_id: The account owner
    - account_id: Which account the transaction affects
    - category_id: How to categorize it
    - counterparty_account_id: Optional opposing account (for transfers)

    Amount is stored as an unsigned Decimal. The direction (debit/credit) is
    determined by combining the `type` field with the account's `type`. For
    example:
    - A PAYMENT from a checking account is a debit (negative balance change)
    - A REFUND to a credit card is a credit (negative balance change)
    - TRANSFER between accounts requires two transactions with opposite signs

    See also:
    - `Account.current_balance`: Tracks running balance (positive=asset, negative=liability)
    - `TransactionType`: Defines the nature of each transaction
    """

    __tablename__ = "transactions"

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
    # Account that this transaction affects
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Category for classification (optional for flexibility)
    category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Counterparty account for transfers (optional)
    counterparty_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Source planned-payment template for audit linkage (optional)
    planned_payment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("planned_payments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Unidirectional audit link back to the source template
    planned_payment: Mapped[PlannedPayment | None] = relationship(
        foreign_keys=[planned_payment_id],
    )
    # Source projected transaction for forecast layer (optional)
    projected_transaction_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "projected_transactions.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_transactions_projected_transaction",
        ),
        nullable=True,
        index=True,
    )
    # Relationship to source projected transaction
    projected_transaction: Mapped[ProjectedTransaction | None] = relationship(
        foreign_keys=[projected_transaction_id],
    )
    # Amount as positive Decimal (direction determined by type + account type)
    amount: Mapped[Money] = mapped_column(
        MONEY_TYPE,
        nullable=False,
    )
    # Transaction type determines the nature of the entry
    type: Mapped[TransactionType] = mapped_column(
        nullable=False,
        index=True,
    )
    # Description for human readability
    description: Mapped[str | None] = mapped_column(
        nullable=True,
        default=None,
    )
    # Date when the transaction is recognized for accounting (accrual basis)
    date_accrual: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
    )
    # Date when actual cash movement occurs
    date_cash: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
    )
    # Optional metadata for reconciliation
    statement_id: Mapped[UUID | None] = mapped_column(
        nullable=True,
        index=True,
    )
    # Whether the transaction has been reconciled with a statement
    is_reconciled: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        index=True,
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

    # Prevent duplicate transactions for the same planned payment occurrence
    __table_args__ = (
        UniqueConstraint(
            "planned_payment_id",
            "date_cash",
            name="uq_planned_payment_date_cash",
        ),
    )
