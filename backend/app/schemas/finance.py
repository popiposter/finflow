"""Finance domain schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.types import AccountType, CategoryType, TransactionType


class AccountBase(BaseModel):
    """Base account schema."""

    name: str
    type: AccountType
    description: str | None = None
    current_balance: Decimal | None = None
    currency_code: str = "USD"
    is_active: bool = True
    opened_at: datetime | None = None
    closed_at: datetime | None = None


class AccountCreate(AccountBase):
    """Schema for account creation."""


class AccountOut(AccountBase):
    """Schema for account responses."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CategoryBase(BaseModel):
    """Base category schema."""

    name: str
    type: CategoryType
    description: str | None = None
    parent_id: UUID | None = None
    is_active: bool = True
    display_order: int = 0


class CategoryCreate(CategoryBase):
    """Schema for category creation."""


class CategoryOut(CategoryBase):
    """Schema for category responses."""

    id: UUID
    user_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionBase(BaseModel):
    """Base transaction schema."""

    account_id: UUID
    category_id: UUID | None = None
    counterparty_account_id: UUID | None = None
    amount: Decimal
    type: TransactionType
    description: str | None = None
    date_accrual: datetime
    date_cash: datetime
    is_reconciled: bool = False


class TransactionCreate(TransactionBase):
    """Schema for transaction creation."""


class TransactionOut(TransactionBase):
    """Schema for transaction responses."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
