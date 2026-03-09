"""Reporting API routes."""

from typing import AsyncGenerator

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user
from app.schemas.auth import UserOut
from app.schemas.finance import (
    CashflowQueryParams,
    CashflowReportResponse,
    PnLQueryParams,
    PnLReportResponse,
)
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


async def get_report_service() -> AsyncGenerator[ReportService, None]:
    """Get report service with database session.

    Yields:
        ReportService instance.
    """
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            yield ReportService(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@router.get(
    "/pnl",
    response_model=PnLReportResponse,
)
async def get_pl_report(
    params: PnLQueryParams = Depends(),
    current_user: UserOut = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> PnLReportResponse:
    """Generate P&L (Profit and Loss) report.

    Aggregates transactions by date_accrual to show financial performance
    over a date range.

    Args:
        params: Query parameters for date range and grouping.
        current_user: Authenticated user.
        service: Report service dependency.

    Returns:
        PnLReportResponse with aggregated totals.
    """
    return await service.get_pl_report(
        user_id=current_user.id,
        query_params=params,
    )


@router.get(
    "/cashflow",
    response_model=CashflowReportResponse,
)
async def get_cashflow_report(
    params: CashflowQueryParams = Depends(),
    current_user: UserOut = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> CashflowReportResponse:
    """Generate cashflow report.

    Aggregates transactions by date_cash to show actual cash movements
    over a date range.

    Args:
        params: Query parameters for date range and grouping.
        current_user: Authenticated user.
        service: Report service dependency.

    Returns:
        CashflowReportResponse with aggregated totals.
    """
    return await service.get_cashflow_report(
        user_id=current_user.id,
        query_params=params,
    )


__all__ = ["router"]
