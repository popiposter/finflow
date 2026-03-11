"""Report repository for aggregation queries."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.projected_transaction import ProjectedTransaction
from app.models.transaction import Transaction
from app.models.types import (
    CategoryType,
    ProjectedTransactionStatus,
    ProjectedTransactionType,
    TransactionType,
)


class ReportRepository:
    """Repository for P&L and cashflow aggregation queries."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.session = session

    async def aggregate_pl(
        self,
        user_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
        group_by: str | None = None,
    ) -> dict:
        """Aggregate P&L data by date_accrual.

        Args:
            user_id: The user's UUID.
            start_date: Start date filter (inclusive). Optional.
            end_date: End date filter (inclusive). Optional.
            group_by: Grouping mode - "by_category" or "by_type". Optional.

        Returns:
            Dict with totals structured for P&L response.
        """
        stmt = select(Transaction).where(Transaction.user_id == user_id)

        if start_date:
            stmt = stmt.where(
                Transaction.date_accrual
                >= datetime.combine(start_date, datetime.min.time())
            )
        if end_date:
            stmt = stmt.where(
                Transaction.date_accrual
                <= datetime.combine(end_date, datetime.max.time())
            )

        # Get all matching transactions
        result = await self.session.scalars(stmt)
        transactions = list(result.all())

        # Calculate totals
        totals_by_category: dict[UUID | None, dict] = {}
        totals_by_type: dict[TransactionType, Decimal] = {}
        grand_total = Decimal("0.00")

        # Get categories for all transactions
        category_ids = {txn.category_id for txn in transactions if txn.category_id}
        categories: dict[UUID, Category] = {}
        if category_ids:
            cat_stmt = select(Category).where(Category.id.in_(category_ids))
            cat_result = await self.session.scalars(cat_stmt)
            categories = {cat.id: cat for cat in cat_result.all()}

        for txn in transactions:
            # Calculate signed amount based on transaction type
            signed_amount = self._get_signed_amount(txn)

            # Aggregate by category
            cat_id = txn.category_id
            if cat_id not in totals_by_category:
                # Get category type from the category object
                cat_type = CategoryType.EXPENSE  # default
                if cat_id and cat_id in categories:
                    cat_type = categories[cat_id].type
                totals_by_category[cat_id] = {
                    "total": Decimal("0.00"),
                    "type": cat_type,
                }
            totals_by_category[cat_id]["total"] += signed_amount

            # Aggregate by type
            if txn.type not in totals_by_type:
                totals_by_type[txn.type] = Decimal("0.00")
            totals_by_type[txn.type] += signed_amount

            # Grand total (absolute sum for display)
            grand_total += abs(signed_amount)

        # Format category totals with category names
        category_totals_formatted = []
        for cat_id, data in totals_by_category.items():
            cat_name = None
            if cat_id and cat_id in categories:
                cat_name = categories[cat_id].name
            category_totals_formatted.append(
                {
                    "category_id": cat_id,
                    "category_name": cat_name,
                    "total": data["total"],
                    "type": data["type"],
                }
            )

        # Format type totals
        type_totals_formatted = [
            {"type": t, "total": total} for t, total in totals_by_type.items()
        ]

        return {
            "totals_by_category": category_totals_formatted,
            "totals_by_type": type_totals_formatted,
            "grand_total": grand_total,
            "start_date": start_date,
            "end_date": end_date,
        }

    async def aggregate_cashflow(
        self,
        user_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
        group_by: str | None = None,
    ) -> dict:
        """Aggregate cashflow data by date_cash.

        Args:
            user_id: The user's UUID.
            start_date: Start date filter (inclusive). Optional.
            end_date: End date filter (inclusive). Optional.
            group_by: Grouping mode - "by_category" or "by_type". Optional.

        Returns:
            Dict with totals structured for cashflow response.
        """
        stmt = select(Transaction).where(Transaction.user_id == user_id)

        if start_date:
            stmt = stmt.where(
                Transaction.date_cash
                >= datetime.combine(start_date, datetime.min.time())
            )
        if end_date:
            stmt = stmt.where(
                Transaction.date_cash <= datetime.combine(end_date, datetime.max.time())
            )

        # Get all matching transactions
        result = await self.session.scalars(stmt)
        transactions = list(result.all())

        # Calculate totals
        totals_by_category: dict[UUID | None, dict] = {}
        totals_by_type: dict[TransactionType, Decimal] = {}
        grand_total = Decimal("0.00")

        # Get categories for all transactions
        category_ids = {txn.category_id for txn in transactions if txn.category_id}
        categories: dict[UUID, Category] = {}
        if category_ids:
            cat_stmt = select(Category).where(Category.id.in_(category_ids))
            cat_result = await self.session.scalars(cat_stmt)
            categories = {cat.id: cat for cat in cat_result.all()}

        for txn in transactions:
            # Calculate signed amount based on transaction type
            signed_amount = self._get_signed_amount(txn)

            # Aggregate by category
            cat_id = txn.category_id
            if cat_id not in totals_by_category:
                # Get category type from the category object
                cat_type = CategoryType.EXPENSE  # default
                if cat_id and cat_id in categories:
                    cat_type = categories[cat_id].type
                totals_by_category[cat_id] = {
                    "total": Decimal("0.00"),
                    "type": cat_type,
                }
            totals_by_category[cat_id]["total"] += signed_amount

            # Aggregate by type
            if txn.type not in totals_by_type:
                totals_by_type[txn.type] = Decimal("0.00")
            totals_by_type[txn.type] += signed_amount

            # Grand total (absolute sum for display)
            grand_total += abs(signed_amount)

        # Format category totals with category names
        category_totals_formatted = []
        for cat_id, data in totals_by_category.items():
            cat_name = None
            if cat_id and cat_id in categories:
                cat_name = categories[cat_id].name
            category_totals_formatted.append(
                {
                    "category_id": cat_id,
                    "category_name": cat_name,
                    "total": data["total"],
                    "type": data["type"],
                }
            )

        # Format type totals
        type_totals_formatted = [
            {"type": t, "total": total} for t, total in totals_by_type.items()
        ]

        return {
            "totals_by_category": category_totals_formatted,
            "totals_by_type": type_totals_formatted,
            "grand_total": grand_total,
            "start_date": start_date,
            "end_date": end_date,
        }

    async def get_transactions_before_cash_date(
        self,
        user_id: UUID,
        before_date: date,
    ) -> list[Transaction]:
        """Get all transactions before a cash date."""
        stmt = (
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.date_cash
                < datetime.combine(before_date, datetime.min.time()),
            )
            .order_by(Transaction.date_cash, Transaction.created_at, Transaction.id)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_transactions_in_cash_date_range(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[Transaction]:
        """Get transactions within a cash-date range."""
        stmt = (
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.date_cash
                >= datetime.combine(start_date, datetime.min.time()),
                Transaction.date_cash
                <= datetime.combine(end_date, datetime.max.time()),
            )
            .order_by(Transaction.date_cash, Transaction.created_at, Transaction.id)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_projected_transactions_in_date_range(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
        include_skipped: bool = False,
    ) -> list[ProjectedTransaction]:
        """Get projected transactions within a projected date range."""
        stmt = (
            select(ProjectedTransaction)
            .where(
                ProjectedTransaction.planned_payment.has(user_id=user_id),
                ProjectedTransaction.projected_date >= start_date,
                ProjectedTransaction.projected_date <= end_date,
            )
            .options(selectinload(ProjectedTransaction.planned_payment))
            .order_by(
                ProjectedTransaction.projected_date,
                ProjectedTransaction.created_at,
                ProjectedTransaction.id,
            )
        )
        if include_skipped:
            stmt = stmt.where(
                ProjectedTransaction.status.in_(
                    [
                        ProjectedTransactionStatus.PENDING,
                        ProjectedTransactionStatus.SKIPPED,
                    ]
                )
            )
        else:
            stmt = stmt.where(
                ProjectedTransaction.status == ProjectedTransactionStatus.PENDING
            )

        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_projected_transactions_between_dates(
        self,
        user_id: UUID,
        start_date: date,
        target_date: date,
    ) -> list[ProjectedTransaction]:
        """Get pending projected transactions between two dates."""
        stmt = (
            select(ProjectedTransaction)
            .where(
                ProjectedTransaction.planned_payment.has(user_id=user_id),
                ProjectedTransaction.status == ProjectedTransactionStatus.PENDING,
                ProjectedTransaction.projected_date >= start_date,
                ProjectedTransaction.projected_date <= target_date,
            )
            .options(selectinload(ProjectedTransaction.planned_payment))
            .order_by(
                ProjectedTransaction.projected_date,
                ProjectedTransaction.created_at,
                ProjectedTransaction.id,
            )
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    def _get_signed_amount(self, txn: Transaction) -> Decimal:
        """Get signed amount for a transaction based on its type.

        For P&L and cashflow reporting:
        - INCOME transactions are positive
        - EXPENSE transactions are negative
        - PAYMENT is negative (money going out)
        - REFUND is positive (money coming back)
        - TRANSFER is neutral (just moving money between accounts)

        Args:
            txn: The transaction to calculate signed amount for.

        Returns:
            Decimal with sign based on transaction type.
        """
        # Income and refunds increase balance
        if txn.type in (TransactionType.INCOME, TransactionType.REFUND):
            return txn.amount
        # Expenses and payments decrease balance
        elif txn.type in (TransactionType.EXPENSE, TransactionType.PAYMENT):
            return -txn.amount
        # Transfers are neutral for P&L/cashflow
        elif txn.type == TransactionType.TRANSFER:
            return Decimal("0.00")
        # Adjustments - treat as positive if not specified
        else:
            return txn.amount

    def get_signed_projected_amount(self, projection: ProjectedTransaction) -> Decimal:
        """Get signed amount for a projected transaction."""
        if projection.type == ProjectedTransactionType.INCOME:
            return projection.projected_amount
        return -projection.projected_amount
