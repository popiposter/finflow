"""Core domain types and conventions for FinFlow finance models.

This module provides shared enums and conventions used across accounts,
categories, and transactions models.
"""

from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from sqlalchemy import Numeric

# Money fields use Decimal/NUMERIC, not float
# This ensures precise monetary calculations
Money = Annotated[Decimal, "Money amount"]

# SQLAlchemy type for money/numeric fields
# Using 18,2 for up to 999,999,999,999,999,999.99
MONEY_TYPE = Numeric(precision=18, scale=2)

# Date/Time conventions
# All timestamps should be timezone-aware (TIMESTAMP with timezone=True)
# See auth models for reference patterns


class AccountType(StrEnum):
    """Supported account types for financial tracking.

    These represent different kinds of accounts users can track:
    - Checking/savings accounts
    - Credit cards
    - Cash wallets
    - Investment accounts
    - Loans
    """

    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    INVESTMENT = "investment"
    LOAN = "loan"
    OTHER = "other"


class CategoryType(StrEnum):
    """Category types for organizing transactions.

    Categories can be nested (hierarchical) via parent_id.
    Top-level categories use parent_id = NULL.
    """

    INCOME = "income"
    EXPENSE = "expense"


class TransactionType(StrEnum):
    """Transaction types for categorizing financial entries.

    This distinguishes between different kinds of transaction flows.
    The actual account debits/credits are tracked separately.
    """

    PAYMENT = "payment"
    REFUND = "refund"
    TRANSFER = "transfer"
    INCOME = "income"
    EXPENSE = "expense"
    ADJUSTMENT = "adjustment"


# Common validation constants
MAX_ACCOUNT_NAME_LENGTH = 100
MAX_CATEGORY_NAME_LENGTH = 100
MAX_TRANSACTION_DESCRIPTION_LENGTH = 500

# Precision for money calculations
MONEY_DECIMAL_PLACES = 2
MONEY_MAX_DIGITS = 18
