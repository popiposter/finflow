"""Unified cashflow ledger read-model service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.projected_transaction import ProjectedTransaction
from app.models.transaction import Transaction
from app.repositories.report_repository import ReportRepository
from app.schemas.finance import (
    CashflowForecastResponse,
    CashflowLedgerMode,
    CashflowLedgerReportResponse,
    CashflowRow,
    CashflowRowType,
)


@dataclass(slots=True)
class _CashflowEntry:
    """Internal normalized cashflow entry."""

    row_type: CashflowRowType
    row_id: UUID
    date: date
    description: str | None
    amount: Decimal
    type: str
    status: str
    created_at_value: datetime
    planned_payment_id: UUID | None
    projected_transaction_id: UUID | None
    transaction_id: UUID | None


class CashflowService:
    """Build unified cashflow ledger and forecast summaries."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service with a database session."""
        self.report_repo = ReportRepository(session)

    async def build_report(
        self,
        user_id: UUID,
        from_date: date,
        to_date: date,
        mode: CashflowLedgerMode = CashflowLedgerMode.MIXED,
        include_skipped: bool = False,
    ) -> CashflowLedgerReportResponse:
        """Build a unified cashflow ledger report."""
        opening_transactions = await self.report_repo.get_transactions_before_cash_date(
            user_id=user_id,
            before_date=from_date,
        )
        opening_balance = sum(
            (self.report_repo._get_signed_amount(txn) for txn in opening_transactions),
            start=Decimal("0.00"),
        )

        entries: list[_CashflowEntry] = []
        if mode != CashflowLedgerMode.PLANNED_ONLY:
            actual_transactions = (
                await self.report_repo.get_transactions_in_cash_date_range(
                    user_id=user_id,
                    start_date=from_date,
                    end_date=to_date,
                )
            )
            entries.extend(self._normalize_transactions(actual_transactions))

        if mode != CashflowLedgerMode.ACTUAL_ONLY:
            projections = (
                await self.report_repo.get_projected_transactions_in_date_range(
                    user_id=user_id,
                    start_date=from_date,
                    end_date=to_date,
                    include_skipped=include_skipped,
                )
            )
            entries.extend(self._normalize_projections(projections))

        sorted_entries = sorted(entries, key=self._sort_key)

        running_balance = opening_balance
        rows: list[CashflowRow] = []
        for entry in sorted_entries:
            running_balance += entry.amount
            rows.append(
                CashflowRow(
                    row_type=entry.row_type,
                    row_id=entry.row_id,
                    date=entry.date,
                    description=entry.description,
                    amount=entry.amount,
                    type=entry.type,
                    status=entry.status,
                    balance_after=running_balance,
                    planned_payment_id=entry.planned_payment_id,
                    projected_transaction_id=entry.projected_transaction_id,
                    transaction_id=entry.transaction_id,
                )
            )

        return CashflowLedgerReportResponse(
            opening_balance=opening_balance,
            closing_balance=running_balance,
            rows=rows,
        )

    async def build_forecast(
        self,
        user_id: UUID,
        target_date: date,
    ) -> CashflowForecastResponse:
        """Build a forecast summary through a target date."""
        today = date.today()
        current_balance_transactions = (
            await self.report_repo.get_transactions_before_cash_date(
                user_id=user_id,
                before_date=today,
            )
        )
        # Include today's actual transactions in current balance.
        current_day_transactions = (
            await self.report_repo.get_transactions_in_cash_date_range(
                user_id=user_id,
                start_date=today,
                end_date=today,
            )
        )
        current_balance = sum(
            (
                self.report_repo._get_signed_amount(txn)
                for txn in [*current_balance_transactions, *current_day_transactions]
            ),
            start=Decimal("0.00"),
        )

        pending_projections = (
            await self.report_repo.get_projected_transactions_between_dates(
                user_id=user_id,
                start_date=today,
                target_date=target_date,
            )
        )
        projected_income = Decimal("0.00")
        projected_expense = Decimal("0.00")
        for projection in pending_projections:
            if projection.type.value == "income":
                projected_income += projection.projected_amount
            else:
                projected_expense += projection.projected_amount

        return CashflowForecastResponse(
            current_balance=current_balance,
            projected_income=projected_income,
            projected_expense=projected_expense,
            projected_balance=current_balance + projected_income - projected_expense,
            pending_count=len(pending_projections),
        )

    def _normalize_transactions(
        self,
        transactions: list[Transaction],
    ) -> list[_CashflowEntry]:
        """Normalize actual transactions into unified entries."""
        entries: list[_CashflowEntry] = []
        for txn in transactions:
            entries.append(
                _CashflowEntry(
                    row_type=CashflowRowType.ACTUAL,
                    row_id=txn.id,
                    date=txn.date_cash.date(),
                    description=txn.description,
                    amount=self.report_repo._get_signed_amount(txn),
                    type=txn.type.value,
                    status="posted",
                    created_at_value=txn.created_at,
                    planned_payment_id=txn.planned_payment_id,
                    projected_transaction_id=txn.projected_transaction_id,
                    transaction_id=txn.id,
                )
            )
        return entries

    def _normalize_projections(
        self,
        projections: list[ProjectedTransaction],
    ) -> list[_CashflowEntry]:
        """Normalize projections into unified entries."""
        entries: list[_CashflowEntry] = []
        for projection in projections:
            entries.append(
                _CashflowEntry(
                    row_type=CashflowRowType.PROJECTED,
                    row_id=projection.id,
                    date=projection.projected_date,
                    description=projection.projected_description,
                    amount=self.report_repo.get_signed_projected_amount(projection),
                    type=projection.type.value,
                    status=projection.status.value,
                    created_at_value=projection.created_at,
                    planned_payment_id=projection.planned_payment_id,
                    projected_transaction_id=projection.id,
                    transaction_id=projection.transaction_id,
                )
            )
        return entries

    def _sort_key(self, entry: _CashflowEntry) -> tuple[date, int, int, datetime, UUID]:
        """Return deterministic sort key for ledger entries."""
        type_order = 0 if entry.amount >= 0 else 1
        row_type_order = 0 if entry.row_type == CashflowRowType.ACTUAL else 1
        return (
            entry.date,
            type_order,
            row_type_order,
            entry.created_at_value,
            entry.row_id,
        )
