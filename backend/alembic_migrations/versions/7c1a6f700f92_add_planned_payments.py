"""add_planned_payments

Revision ID: 7c1a6f700f92
Revises: 20260307120000
Create Date: 2026-03-09 11:15:42.018177

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7c1a6f700f92"
down_revision: Union[str, None] = "20260307120000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create recurrence enum type
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE recurrence AS ENUM ('daily', 'weekly', 'monthly');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END
        $$;
        """
    )

    # Planned payments table
    op.create_table(
        "planned_payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "recurrence",
            postgresql.ENUM(
                "daily",
                "weekly",
                "monthly",
                name="recurrence",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("next_due_at", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(
        "ix_planned_payments_user_id", "planned_payments", ["user_id"], unique=False
    )
    op.create_index(
        "ix_planned_payments_account_id",
        "planned_payments",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        "ix_planned_payments_category_id",
        "planned_payments",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        "ix_planned_payments_recurrence",
        "planned_payments",
        ["recurrence"],
        unique=False,
    )
    op.create_index(
        "ix_planned_payments_start_date",
        "planned_payments",
        ["start_date"],
        unique=False,
    )
    op.create_index(
        "ix_planned_payments_end_date", "planned_payments", ["end_date"], unique=False
    )
    op.create_index(
        "ix_planned_payments_next_due_at",
        "planned_payments",
        ["next_due_at"],
        unique=False,
    )
    op.create_index(
        "ix_planned_payments_is_active", "planned_payments", ["is_active"], unique=False
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop indexes
    op.drop_index("ix_planned_payments_is_active", table_name="planned_payments")
    op.drop_index("ix_planned_payments_next_due_at", table_name="planned_payments")
    op.drop_index("ix_planned_payments_end_date", table_name="planned_payments")
    op.drop_index("ix_planned_payments_start_date", table_name="planned_payments")
    op.drop_index("ix_planned_payments_recurrence", table_name="planned_payments")
    op.drop_index("ix_planned_payments_category_id", table_name="planned_payments")
    op.drop_index("ix_planned_payments_account_id", table_name="planned_payments")
    op.drop_index("ix_planned_payments_user_id", table_name="planned_payments")

    # Drop table
    op.drop_table("planned_payments")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS recurrence")
