"""Parse-and-create transaction schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.types import TransactionType


class ParseRequest(BaseModel):
    """Request schema for parse-and-create endpoint."""

    text: str
    """Free-form text to parse (e.g., 'продукты во вкусвилле 1500 рублей')."""

    account_id: UUID | None = None
    """Target account ID. Required until default account selection is implemented."""

    category_id: UUID | None = None
    """Optional category override. If omitted, transaction stays uncategorized."""


class ParsedResult(BaseModel):
    """Result of parsing free-form text."""

    amount: Decimal | None = None
    """Extracted amount from the text, if any."""

    description: str | None = None
    """Extracted description or payee name."""

    category_name: str | None = None
    """Extracted category name if detectable from text."""

    transaction_type: TransactionType = TransactionType.EXPENSE
    """Inferred transaction type from parser heuristics."""

    original_text: str
    """Original text that was parsed (always preserved)."""


class TransactionCreateRequest(BaseModel):
    """Request to create a transaction with parsed data."""

    text: str
    """Original free-form text (for preservation)."""

    account_id: UUID | None = None
    """Optional account ID. If None, uses user's default account."""

    category_id: UUID | None = None
    """Optional category ID. If None, leaves transaction uncategorized."""


class ParseAndCreateResponse(BaseModel):
    """Response from parse-and-create endpoint."""

    id: UUID
    """Transaction ID."""

    user_id: UUID
    """User who owns this transaction."""

    account_id: UUID
    """Account this transaction affects."""

    category_id: UUID | None
    """Category ID, or None if uncategorized."""

    amount: Decimal
    """Transaction amount."""

    type: str
    """Transaction type (inferred from context)."""

    description: str
    """Description with original text preserved."""

    date_accrual: datetime
    """Accrual date."""

    date_cash: datetime
    """Cash movement date."""

    is_reconciled: bool
    """Whether transaction is reconciled."""


class ParseErrorResponse(BaseModel):
    """Error response when parsing fails."""

    error: str
    """Error message."""

    detail: str | None = None
    """Optional additional detail."""
