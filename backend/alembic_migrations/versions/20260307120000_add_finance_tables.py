"""Add finance domain tables: accounts, categories, transactions.

Revision ID: 20260307120000
Revises: 20260306210000
Create Date: 2026-03-07 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260307120000"
down_revision: Union[str, None] = "20260306210000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Enum types for finance domain
    # Use idempotent enum creation so a partially failed local bootstrap can rerun safely.
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE account_type AS ENUM (
                'checking',
                'savings',
                'credit_card',
                'cash',
                'investment',
                'loan',
                'other'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE category_type AS ENUM ('income', 'expense');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE transaction_type AS ENUM (
                'payment',
                'refund',
                'transfer',
                'income',
                'expense',
                'adjustment'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END
        $$;
        """
    )

    # Accounts table
    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM(
                "checking",
                "savings",
                "credit_card",
                "cash",
                "investment",
                "loan",
                "other",
                name="account_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("current_balance", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("currency_code", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("opened_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("closed_at", sa.TIMESTAMP(timezone=True), nullable=True),
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
    )
    op.create_index("ix_accounts_user_id", "accounts", ["user_id"], unique=False)
    op.create_index("ix_accounts_type", "accounts", ["type"], unique=False)
    op.create_index(
        "ix_accounts_currency_code", "accounts", ["currency_code"], unique=False
    )
    op.create_index("ix_accounts_is_active", "accounts", ["is_active"], unique=False)
    op.create_index("ix_accounts_name", "accounts", ["name"], unique=False)

    # Categories table with hierarchical support
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "type",
            postgresql.ENUM(
                "income",
                "expense",
                name="category_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_categories_user_id", "categories", ["user_id"], unique=False)
    op.create_index("ix_categories_type", "categories", ["type"], unique=False)
    op.create_index(
        "ix_categories_parent_id", "categories", ["parent_id"], unique=False
    )
    op.create_index(
        "ix_categories_is_active", "categories", ["is_active"], unique=False
    )
    op.create_index("ix_categories_name", "categories", ["name"], unique=False)

    # Transactions table
    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column("counterparty_account_id", sa.Uuid(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM(
                "payment",
                "refund",
                "transfer",
                "income",
                "expense",
                "adjustment",
                name="transaction_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("date_accrual", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("date_cash", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("statement_id", sa.Uuid(), nullable=True),
        sa.Column("is_reconciled", sa.Boolean(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["counterparty_account_id"], ["accounts.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(
        "ix_transactions_user_id", "transactions", ["user_id"], unique=False
    )
    op.create_index(
        "ix_transactions_account_id", "transactions", ["account_id"], unique=False
    )
    op.create_index(
        "ix_transactions_category_id", "transactions", ["category_id"], unique=False
    )
    op.create_index(
        "ix_transactions_counterparty_account_id",
        "transactions",
        ["counterparty_account_id"],
        unique=False,
    )
    op.create_index("ix_transactions_type", "transactions", ["type"], unique=False)
    op.create_index(
        "ix_transactions_date_accrual", "transactions", ["date_accrual"], unique=False
    )
    op.create_index(
        "ix_transactions_date_cash", "transactions", ["date_cash"], unique=False
    )
    op.create_index(
        "ix_transactions_statement_id", "transactions", ["statement_id"], unique=False
    )
    op.create_index(
        "ix_transactions_is_reconciled", "transactions", ["is_reconciled"], unique=False
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop transactions table first (has foreign keys to categories and accounts)
    op.drop_index("ix_transactions_is_reconciled", table_name="transactions")
    op.drop_index("ix_transactions_statement_id", table_name="transactions")
    op.drop_index("ix_transactions_date_cash", table_name="transactions")
    op.drop_index("ix_transactions_date_accrual", table_name="transactions")
    op.drop_index("ix_transactions_type", table_name="transactions")
    op.drop_index("ix_transactions_counterparty_account_id", table_name="transactions")
    op.drop_index("ix_transactions_category_id", table_name="transactions")
    op.drop_index("ix_transactions_account_id", table_name="transactions")
    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_table("transactions")

    # Drop categories table (has foreign key to itself and users)
    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_index("ix_categories_is_active", table_name="categories")
    op.drop_index("ix_categories_parent_id", table_name="categories")
    op.drop_index("ix_categories_type", table_name="categories")
    op.drop_index("ix_categories_user_id", table_name="categories")
    op.drop_table("categories")

    # Drop accounts table (has foreign key to users)
    op.drop_index("ix_accounts_name", table_name="accounts")
    op.drop_index("ix_accounts_is_active", table_name="accounts")
    op.drop_index("ix_accounts_currency_code", table_name="accounts")
    op.drop_index("ix_accounts_type", table_name="accounts")
    op.drop_index("ix_accounts_user_id", table_name="accounts")
    op.drop_table("accounts")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS transaction_type")
    op.execute("DROP TYPE IF EXISTS category_type")
    op.execute("DROP TYPE IF EXISTS account_type")
