"""Schemas for LLM-assisted transaction parsing."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.types import TransactionType


class LLMTransactionParse(BaseModel):
    """Structured parse payload expected back from the LLM."""

    amount: Decimal | None = None
    currency_code: str | None = None
    transaction_type: TransactionType = TransactionType.EXPENSE
    description: str | None = None
    merchant: str | None = None
    transaction_date: date | None = Field(default=None, alias="date")
    category_hint: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    needs_confirmation: bool = False
    reason: str | None = None

    model_config = {"populate_by_name": True}
