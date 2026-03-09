"""add_planned_payment_to_transactions

Revision ID: 9674289f1982
Revises: 7c1a6f700f92
Create Date: 2026-03-09 12:06:09.322585

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9674289f1982"
down_revision: Union[str, None] = "7c1a6f700f92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Add planned_payment_id column to transactions table
    op.add_column(
        "transactions",
        sa.Column(
            "planned_payment_id",
            sa.Uuid(),
            nullable=True,
        ),
    )
    op.create_foreign_constraint(
        "fk_transactions_planned_payment",
        "transactions",
        "planned_payments",
        ["planned_payment_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_transactions_planned_payment_id",
        "transactions",
        ["planned_payment_id"],
        unique=False,
    )

    # Add unique constraint for idempotency: prevent duplicate transactions
    # for the same planned payment occurrence (same date_cash)
    op.execute(
        """
        CREATE UNIQUE INDEX uq_transactions_planned_payment_date_cash
        ON transactions (planned_payment_id, date_cash)
        WHERE planned_payment_id IS NOT NULL
        """
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop unique index for idempotency
    op.execute("DROP INDEX IF EXISTS uq_transactions_planned_payment_date_cash")
    op.drop_index("ix_transactions_planned_payment_id", table_name="transactions")
    op.drop_constraint(
        "fk_transactions_planned_payment",
        "transactions",
        type_="foreignkey",
    )
    op.drop_column("transactions", "planned_payment_id")
