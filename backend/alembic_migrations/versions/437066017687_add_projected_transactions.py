"""add_projected_transactions

Revision ID: 437066017687
Revises: 9674289f1982
Create Date: 2026-03-10 00:29:20.487121

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "437066017687"
down_revision: Union[str, None] = "9674289f1982"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create projected transaction status enum
    op.execute(
        "CREATE TYPE projected_transaction_status AS ENUM ('pending', 'confirmed', 'skipped')"
    )
    # Create projected transaction type enum
    op.execute(
        "CREATE TYPE projected_transaction_type AS ENUM ('income', 'expense')"
    )

    # Projected transactions table
    op.create_table(
        "projected_transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("planned_payment_id", sa.Uuid(), nullable=False),
        sa.Column("origin_date", sa.Date(), nullable=False),
        sa.Column("origin_amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("origin_description", sa.String(), nullable=True),
        sa.Column("origin_category_id", sa.Uuid(), nullable=True),
        sa.Column(
            "type",
            sa.Enum("income", "expense", name="projected_transaction_type"),
            nullable=False,
        ),
        sa.Column("projected_date", sa.Date(), nullable=False),
        sa.Column("projected_amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("projected_description", sa.String(), nullable=True),
        sa.Column("projected_category_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "confirmed", "skipped", name="projected_transaction_status"),
            nullable=False,
        ),
        sa.Column("transaction_id", sa.Uuid(), nullable=True),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["planned_payment_id"],
            ["planned_payments.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["origin_category_id"],
            ["categories.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["projected_category_id"],
            ["categories.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_projected_transactions_planned_payment_id",
        "projected_transactions",
        ["planned_payment_id"],
        unique=False,
    )
    op.create_index(
        "ix_projected_transactions_origin_date",
        "projected_transactions",
        ["origin_date"],
        unique=False,
    )
    op.create_index(
        "ix_projected_transactions_projected_date",
        "projected_transactions",
        ["projected_date"],
        unique=False,
    )
    op.create_index(
        "ix_projected_transactions_status",
        "projected_transactions",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_projected_transactions_transaction_id",
        "projected_transactions",
        ["transaction_id"],
        unique=False,
    )
    # Add unique constraint to prevent duplicate projections
    op.execute(
        """
        CREATE UNIQUE INDEX uq_projected_transactions_planned_payment_origin_date
        ON projected_transactions (planned_payment_id, origin_date)
        """
    )

    # Add projected_transaction_id column to transactions table
    op.add_column(
        "transactions",
        sa.Column(
            "projected_transaction_id",
            sa.Uuid(),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_transactions_projected_transaction",
        "transactions",
        "projected_transactions",
        ["projected_transaction_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_transactions_projected_transaction_id",
        "transactions",
        ["projected_transaction_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop index on transactions table
    op.drop_index(
        "ix_transactions_projected_transaction_id",
        table_name="transactions",
    )
    op.drop_constraint(
        "fk_transactions_projected_transaction",
        "transactions",
        type_="foreignkey",
    )
    op.drop_column("transactions", "projected_transaction_id")

    # Drop projected transactions unique index
    op.execute("DROP INDEX IF EXISTS uq_projected_transactions_planned_payment_origin_date")

    # Drop projected transactions indexes
    op.drop_index(
        "ix_projected_transactions_transaction_id",
        table_name="projected_transactions",
    )
    op.drop_index(
        "ix_projected_transactions_status",
        table_name="projected_transactions",
    )
    op.drop_index(
        "ix_projected_transactions_projected_date",
        table_name="projected_transactions",
    )
    op.drop_index(
        "ix_projected_transactions_origin_date",
        table_name="projected_transactions",
    )
    op.drop_index(
        "ix_projected_transactions_planned_payment_id",
        table_name="projected_transactions",
    )

    # Drop projected transactions table
    op.drop_table("projected_transactions")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS projected_transaction_type")
    op.execute("DROP TYPE IF EXISTS projected_transaction_status")
