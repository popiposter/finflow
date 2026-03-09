"""Finance domain schemas."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.models.types import AccountType, CategoryType, Recurrence, TransactionType


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


class PlannedPaymentBase(BaseModel):
    """Base planned payment schema."""

    account_id: UUID
    category_id: UUID | None = None
    amount: Decimal
    description: str | None = None
    recurrence: Recurrence
    start_date: date
    end_date: date | None = None
    next_due_at: date | None = None
    is_active: bool = True


class PlannedPaymentCreate(PlannedPaymentBase):
    """Schema for planned payment creation."""


class PlannedPaymentOut(BaseModel):
    """Schema for planned payment responses."""

    id: UUID
    user_id: UUID
    account_id: UUID
    category_id: UUID | None
    amount: Decimal
    description: str | None
    recurrence: Recurrence
    start_date: date
    end_date: date | None
    next_due_at: date
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecurrenceGenerationResult(BaseModel):
    """Result of generating recurring transactions for a single planned payment."""

    planned_payment_id: UUID
    generated_transactions: list[UUID]
    next_due_at: date
    skipped_occurrences: int = 0


class PlannedPaymentExecutionSummary(BaseModel):
    """Summary of a planned payment execution run."""

    total_processed: int
    total_generated: int
    skipped_occurrences: int
    details: list[RecurrenceGenerationResult]


class PlannedPaymentExecutionRequest(BaseModel):
    """Request schema for planned payment execution endpoint."""

    as_of_date: date | None = None
    max_occurrences: int = 100


# === Report Schemas ===


class ReportDateRange(BaseModel):
    """Date range filter for reports."""

    start_date: date
    end_date: date


class ReportGroupBy(StrEnum):
    """Grouping modes for report aggregation."""

    BY_CATEGORY = "by_category"
    BY_TYPE = "by_type"


class PnLQueryParams(BaseModel):
    """Query parameters for P&L report."""

    start_date: date | None = None
    end_date: date | None = None
    group_by: ReportGroupBy | None = None


class CashflowQueryParams(BaseModel):
    """Query parameters for cashflow report."""

    start_date: date | None = None
    end_date: date | None = None
    group_by: ReportGroupBy | None = None


class ReportCategoryTotal(BaseModel):
    """Aggregated total for a category in a report."""

    category_id: UUID | None
    category_name: str | None
    total: Decimal
    type: CategoryType


class ReportTypeTotal(BaseModel):
    """Aggregated total for a transaction type in a report."""

    type: TransactionType
    total: Decimal


class PnLReportResponse(BaseModel):
    """Response model for P&L report."""

    date_accrual_start: date
    date_accrual_end: date
    totals_by_category: list[ReportCategoryTotal]
    totals_by_type: list[ReportTypeTotal]
    grand_total: Decimal


class CashflowReportResponse(BaseModel):
    """Response model for cashflow report."""

    date_cash_start: date
    date_cash_end: date
    totals_by_category: list[ReportCategoryTotal]
    totals_by_type: list[ReportTypeTotal]
    grand_total: Decimal
