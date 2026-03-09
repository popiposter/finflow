"""Service for P&L and cashflow report aggregation."""

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.report_repository import ReportRepository
from app.schemas.finance import (
    CashflowQueryParams,
    CashflowReportResponse,
    PnLQueryParams,
    PnLReportResponse,
    ReportCategoryTotal,
    ReportTypeTotal,
)


class ReportService:
    """Service for generating P&L and cashflow reports."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.report_repo = ReportRepository(session)

    async def get_pl_report(
        self,
        user_id: UUID,
        query_params: PnLQueryParams,
    ) -> PnLReportResponse:
        """Generate P&L report for the given user and date range.

        Args:
            user_id: The user's UUID.
            query_params: Query parameters including date range and grouping.

        Returns:
            PnLReportResponse with aggregated data.
        """
        # Determine effective date range
        start_date = query_params.start_date
        end_date = query_params.end_date

        # Get aggregated data from repository
        agg_data = await self.report_repo.aggregate_pl(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            group_by=query_params.group_by,
        )

        # Build category totals
        category_totals = [
            ReportCategoryTotal(
                category_id=item["category_id"],
                category_name=item["category_name"],
                total=item["total"],
                type=item["type"],
            )
            for item in agg_data["totals_by_category"]
        ]

        # Build type totals
        type_totals = [
            ReportTypeTotal(
                type=item["type"],
                total=item["total"],
            )
            for item in agg_data["totals_by_type"]
        ]

        return PnLReportResponse(
            date_accrual_start=start_date or date.min,
            date_accrual_end=end_date or date.max,
            totals_by_category=category_totals,
            totals_by_type=type_totals,
            grand_total=agg_data["grand_total"],
        )

    async def get_cashflow_report(
        self,
        user_id: UUID,
        query_params: CashflowQueryParams,
    ) -> CashflowReportResponse:
        """Generate cashflow report for the given user and date range.

        Args:
            user_id: The user's UUID.
            query_params: Query parameters including date range and grouping.

        Returns:
            CashflowReportResponse with aggregated data.
        """
        # Determine effective date range
        start_date = query_params.start_date
        end_date = query_params.end_date

        # Get aggregated data from repository
        agg_data = await self.report_repo.aggregate_cashflow(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            group_by=query_params.group_by,
        )

        # Build category totals
        category_totals = [
            ReportCategoryTotal(
                category_id=item["category_id"],
                category_name=item["category_name"],
                total=item["total"],
                type=item["type"],
            )
            for item in agg_data["totals_by_category"]
        ]

        # Build type totals
        type_totals = [
            ReportTypeTotal(
                type=item["type"],
                total=item["total"],
            )
            for item in agg_data["totals_by_type"]
        ]

        return CashflowReportResponse(
            date_cash_start=start_date or date.min,
            date_cash_end=end_date or date.max,
            totals_by_category=category_totals,
            totals_by_type=type_totals,
            grand_total=agg_data["grand_total"],
        )
