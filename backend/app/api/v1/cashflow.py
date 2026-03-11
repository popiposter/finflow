"""Unified cashflow ledger API routes."""

from datetime import date, timedelta
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import get_current_user
from app.schemas.auth import UserOut
from app.schemas.finance import (
    CashflowForecastResponse,
    CashflowLedgerMode,
    CashflowLedgerReportResponse,
)
from app.services.cashflow_service import CashflowService

router = APIRouter(prefix="/cashflow", tags=["cashflow"])


async def get_cashflow_service() -> AsyncGenerator[CashflowService, None]:
    """Get cashflow service with database session."""
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            yield CashflowService(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@router.get("/report", response_model=CashflowLedgerReportResponse)
async def get_cashflow_ledger_report(
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
    mode: CashflowLedgerMode = Query(default=CashflowLedgerMode.MIXED),
    include_skipped: bool = Query(default=False),
    current_user: UserOut = Depends(get_current_user),
    service: CashflowService = Depends(get_cashflow_service),
) -> CashflowLedgerReportResponse:
    """Return the unified cashflow ledger for a date range."""
    return await service.build_report(
        user_id=current_user.id,
        from_date=from_date,
        to_date=to_date,
        mode=mode,
        include_skipped=include_skipped,
    )


@router.get("/forecast", response_model=CashflowForecastResponse)
async def get_cashflow_forecast(
    target_date: date | None = Query(default=None),
    current_user: UserOut = Depends(get_current_user),
    service: CashflowService = Depends(get_cashflow_service),
) -> CashflowForecastResponse:
    """Return the forecast summary through a target date."""
    effective_target_date = target_date or (date.today() + timedelta(days=30))
    return await service.build_forecast(
        user_id=current_user.id,
        target_date=effective_target_date,
    )
