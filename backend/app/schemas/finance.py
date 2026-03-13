"""Finance domain schemas."""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.types import (
    AccountType,
    CategoryType,
    ProjectedTransactionStatus,
    ProjectedTransactionType,
    Recurrence,
    TransactionType,
)


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


class TransactionPatch(BaseModel):
    """Schema for partial transaction updates."""

    amount: Decimal | None = Field(default=None, gt=0)
    category_id: UUID | None = None
    description: str | None = None
    date_accrual: datetime | None = None
    date_cash: datetime | None = None
    is_reconciled: bool | None = None


class TransactionOut(TransactionBase):
    """Schema for transaction responses."""

    id: UUID
    user_id: UUID
    planned_payment_id: UUID | None = None
    projected_transaction_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionImportError(BaseModel):
    """Per-row import error during bulk transaction ingestion."""

    row_number: int
    message: str


class TransactionImportResponse(BaseModel):
    """Summary for workbook-based transaction import."""

    imported_count: int
    imported_transaction_ids: list[UUID]
    skipped_count: int = 0
    errors: list[TransactionImportError] = Field(default_factory=list)


class PlannedPaymentBase(BaseModel):
    """Base planned-payment template schema."""

    account_id: UUID
    category_id: UUID | None = None
    amount: Decimal
    description: str | None = None
    recurrence: Recurrence
    start_date: date_type
    end_date: date_type | None = None
    next_due_at: date_type | None = None
    is_active: bool = True


class PlannedPaymentCreate(PlannedPaymentBase):
    """Schema for planned-payment template creation."""


class PlannedPaymentOut(BaseModel):
    """Schema for planned-payment template responses."""

    id: UUID
    user_id: UUID
    account_id: UUID
    category_id: UUID | None
    amount: Decimal
    description: str | None
    recurrence: Recurrence
    start_date: date_type
    end_date: date_type | None
    next_due_at: date_type
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectionGenerationResult(BaseModel):
    """Result of generating projected transactions for a planned payment."""

    planned_payment_id: UUID
    generated_projections: list[UUID]
    next_due_at: date_type
    skipped_occurrences: int = 0


class CashflowLedgerMode(StrEnum):
    """Supported modes for unified cashflow ledger responses."""

    MIXED = "mixed"
    ACTUAL_ONLY = "actual_only"
    PLANNED_ONLY = "planned_only"


class CashflowRowType(StrEnum):
    """Row source types in the unified cashflow ledger."""

    ACTUAL = "actual"
    PROJECTED = "projected"


class CashflowRow(BaseModel):
    """Unified cashflow ledger row."""

    row_type: CashflowRowType
    row_id: UUID
    date: date_type
    description: str | None = None
    amount: Decimal
    type: str
    status: str
    balance_after: Decimal
    planned_payment_id: UUID | None = None
    projected_transaction_id: UUID | None = None
    transaction_id: UUID | None = None


class CashflowLedgerReportResponse(BaseModel):
    """Unified cashflow ledger response."""

    opening_balance: Decimal
    closing_balance: Decimal
    rows: list[CashflowRow]


class CashflowForecastResponse(BaseModel):
    """Cashflow forecast summary through a target horizon."""

    current_balance: Decimal
    projected_income: Decimal
    projected_expense: Decimal
    projected_balance: Decimal
    pending_count: int


# === Report Schemas ===


class ReportDateRange(BaseModel):
    """Date range filter for reports."""

    start_date: date_type
    end_date: date_type


class ReportGroupBy(StrEnum):
    """Grouping modes for report aggregation."""

    BY_CATEGORY = "by_category"
    BY_TYPE = "by_type"


class PnLQueryParams(BaseModel):
    """Query parameters for P&L report."""

    start_date: date_type | None = None
    end_date: date_type | None = None
    group_by: ReportGroupBy | None = None


class CashflowQueryParams(BaseModel):
    """Query parameters for cashflow report."""

    start_date: date_type | None = None
    end_date: date_type | None = None
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

    date_accrual_start: date_type
    date_accrual_end: date_type
    totals_by_category: list[ReportCategoryTotal]
    totals_by_type: list[ReportTypeTotal]
    grand_total: Decimal


class CashflowReportResponse(BaseModel):
    """Response model for cashflow report."""

    date_cash_start: date_type
    date_cash_end: date_type
    totals_by_category: list[ReportCategoryTotal]
    totals_by_type: list[ReportTypeTotal]
    grand_total: Decimal


# === Projected Transaction Schemas ===


class ProjectedTransactionBase(BaseModel):
    """Base projected transaction schema."""

    planned_payment_id: UUID
    origin_date: date_type
    origin_amount: Decimal
    origin_description: str | None = None
    origin_category_id: UUID | None = None
    type: ProjectedTransactionType


class ProjectedTransactionCreate(ProjectedTransactionBase):
    """Schema for projected transaction creation."""


class ProjectedTransactionOut(BaseModel):
    """Schema for projected transaction responses."""

    id: UUID
    planned_payment_id: UUID
    origin_date: date_type
    origin_amount: Decimal
    origin_description: str | None
    origin_category_id: UUID | None
    type: ProjectedTransactionType
    projected_date: date_type
    projected_amount: Decimal
    projected_description: str | None
    projected_category_id: UUID | None
    status: ProjectedTransactionStatus
    transaction_id: UUID | None
    resolved_at: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectedTransactionUpdate(BaseModel):
    """Schema for updating a projected transaction."""

    projected_amount: Decimal | None = None
    projected_date: date_type | None = None
    projected_description: str | None = None
    projected_category_id: UUID | None = None


class ProjectedTransactionConfirmRequest(BaseModel):
    """Schema for confirming a projected transaction with optional overrides."""

    amount: Decimal | None = None
    date: date_type | None = None
    description: str | None = None
    category_id: UUID | None = None


class ProjectedTransactionConfirmResponse(BaseModel):
    """Response for confirming a projected transaction."""

    projected_transaction: ProjectedTransactionOut
    transaction_id: UUID
