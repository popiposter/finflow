"""Service for managing projected transactions."""

from datetime import date, datetime, time, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import InvalidProjectionStatusError, ProjectionNotFoundError
from app.models.projected_transaction import ProjectedTransaction
from app.models.types import (
    ProjectedTransactionStatus,
    ProjectedTransactionType,
    TransactionType,
)
from app.repositories.projected_transaction_repository import ProjectedTransactionRepository
from app.repositories.transaction_repository import TransactionRepository


class ProjectedTransactionService:
    """Service for managing projected transactions.

    This service provides CRUD operations for projected transactions:
    - update_projection: Edit a pending projection
    - confirm_projection: Confirm a projection (creates actual transaction)
    - skip_projection: Skip a projection (no transaction created)

    Status transitions:
    - PENDING → CONFIRMED: Creates actual Transaction atomically
    - PENDING → SKIPPED: Skips the occurrence, no transaction created
    """

    def __init__(self, session: AsyncSession):
        """Initialize the service with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.session = session
        self.projected_transaction_repo = ProjectedTransactionRepository(session)
        self.transaction_repo = TransactionRepository(session)

    async def update_projection(
        self,
        user_id: UUID,
        projected_transaction_id: UUID,
        projected_amount: Decimal | None = None,
        projected_date: date | None = None,
        projected_description: str | None = None,
        projected_category_id: UUID | None = None,
    ) -> ProjectedTransaction:
        """Update a pending projection.

        Args:
            user_id: The user's UUID (for authorization).
            projected_transaction_id: The projected transaction's UUID.
            projected_amount: New projected amount (optional).
            projected_date: New projected date (optional).
            projected_description: New projected description (optional).
            projected_category_id: New projected category_id (optional).

        Returns:
            The updated projected transaction.

        Raises:
            ProjectionNotFoundError: If projection not found or not owned by user.
            InvalidProjectionStatusError: If status != PENDING.
        """
        projected_transaction = await self.projected_transaction_repo.get_by_user_and_id(
            user_id=user_id,
            projected_transaction_id=projected_transaction_id,
        )

        if projected_transaction is None:
            raise ProjectionNotFoundError(str(projected_transaction_id))

        if projected_transaction.status != ProjectedTransactionStatus.PENDING:
            raise InvalidProjectionStatusError(
                projected_transaction_id=str(projected_transaction.id),
                status=projected_transaction.status,
                allowed_statuses=["PENDING"],
            )

        # Update only provided fields
        if projected_amount is not None:
            projected_transaction.projected_amount = projected_amount
        if projected_date is not None:
            projected_transaction.projected_date = projected_date
        if projected_description is not None:
            projected_transaction.projected_description = projected_description
        if projected_category_id is not None:
            projected_transaction.projected_category_id = projected_category_id

        # Increment version for optimistic locking
        projected_transaction.version += 1

        updated = await self.projected_transaction_repo.update(projected_transaction)
        return updated

    async def confirm_projection(
        self,
        user_id: UUID,
        projected_transaction_id: UUID,
        amount: Decimal | None = None,
        date_: date | datetime | None = None,
        description: str | None = None,
        category_id: UUID | None = None,
    ) -> tuple[ProjectedTransaction, UUID]:
        """Confirm a projection, creating an actual transaction.

        This operation is atomic - both the transaction creation and projection
        update happen in the same database transaction.

        Args:
            user_id: The user's UUID (for authorization).
            projected_transaction_id: The projected transaction's UUID.
            amount: Override amount (optional, defaults to projected_amount).
            date_: Override date (optional, defaults to projected_date).
            description: Override description (optional, defaults to projected_description).
            category_id: Override category_id (optional, defaults to projected_category_id).

        Returns:
            Tuple of (updated projected transaction, created transaction ID).

        Raises:
            ProjectionNotFoundError: If projection not found or not owned by user.
            InvalidProjectionStatusError: If status != PENDING.
        """
        projected_transaction = await self.projected_transaction_repo.get_by_user_and_id(
            user_id=user_id,
            projected_transaction_id=projected_transaction_id,
        )

        if projected_transaction is None:
            raise ProjectionNotFoundError(str(projected_transaction_id))

        if projected_transaction.status != ProjectedTransactionStatus.PENDING:
            raise InvalidProjectionStatusError(
                projected_transaction_id=str(projected_transaction.id),
                status=projected_transaction.status,
                allowed_statuses=["PENDING"],
            )

        # Use projected values as defaults, override if provided
        confirm_amount = (
            amount if amount is not None else projected_transaction.projected_amount
        )
        confirm_date = (
            date_ if date_ is not None else projected_transaction.projected_date
        )
        if isinstance(confirm_date, datetime):
            confirm_date = confirm_date.date()
        confirm_description = (
            description
            if description is not None
            else projected_transaction.projected_description
        )
        confirm_category_id = (
            category_id
            if category_id is not None
            else projected_transaction.projected_category_id
        )

        # Map ProjectedTransactionType to TransactionType
        type_map = {
            ProjectedTransactionType.INCOME: TransactionType.INCOME,
            ProjectedTransactionType.EXPENSE: TransactionType.EXPENSE,
        }
        transaction_type = type_map[projected_transaction.type]

        # Create the actual transaction
        transaction = await self.transaction_repo.create(
            user_id=user_id,
            account_id=projected_transaction.planned_payment.account_id,
            amount=confirm_amount,
            type_=transaction_type,
            date_accrual=datetime.combine(confirm_date, time.min, tzinfo=timezone.utc),
            date_cash=datetime.combine(confirm_date, time.min, tzinfo=timezone.utc),
            category_id=confirm_category_id,
            planned_payment_id=projected_transaction.planned_payment_id,
            projected_transaction_id=projected_transaction.id,
            description=confirm_description,
            is_reconciled=False,
        )

        # Update projection status
        resolved_at = datetime.now(projected_transaction.created_at.tzinfo)
        updated = await self.projected_transaction_repo.confirm_projection(
            projected_transaction=projected_transaction,
            transaction_id=transaction.id,
            resolved_at=resolved_at,
        )

        return updated, transaction.id

    async def skip_projection(
        self,
        user_id: UUID,
        projected_transaction_id: UUID,
    ) -> ProjectedTransaction:
        """Skip a projection.

        Args:
            user_id: The user's UUID (for authorization).
            projected_transaction_id: The projected transaction's UUID.

        Returns:
            The updated projected transaction.

        Raises:
            ProjectionNotFoundError: If projection not found or not owned by user.
            InvalidProjectionStatusError: If status != PENDING.
        """
        projected_transaction = await self.projected_transaction_repo.get_by_user_and_id(
            user_id=user_id,
            projected_transaction_id=projected_transaction_id,
        )

        if projected_transaction is None:
            raise ProjectionNotFoundError(str(projected_transaction_id))

        if projected_transaction.status != ProjectedTransactionStatus.PENDING:
            raise InvalidProjectionStatusError(
                projected_transaction_id=str(projected_transaction.id),
                status=projected_transaction.status,
                allowed_statuses=["PENDING"],
            )

        resolved_at = datetime.now(projected_transaction.created_at.tzinfo)
        updated = await self.projected_transaction_repo.skip_projection(
            projected_transaction=projected_transaction,
            resolved_at=resolved_at,
        )

        return updated

    async def get_projection(
        self,
        user_id: UUID,
        projected_transaction_id: UUID,
    ) -> ProjectedTransaction | None:
        """Get a specific projected transaction.

        Args:
            user_id: The user's UUID (for authorization).
            projected_transaction_id: The projected transaction's UUID.

        Returns:
            The projected transaction if found, None otherwise.
        """
        return await self.projected_transaction_repo.get_by_user_and_id(
            user_id=user_id,
            projected_transaction_id=projected_transaction_id,
        )

    async def list_projections(
        self,
        user_id: UUID,
        status: ProjectedTransactionStatus | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[ProjectedTransaction]:
        """List projected transactions for a user.

        Args:
            user_id: The user's UUID.
            status: Filter by status (optional).
            from_date: Filter by from date (optional).
            to_date: Filter by to date (optional).

        Returns:
            List of projected transactions matching the filters.
        """
        return await self.projected_transaction_repo.get_filtered(
            user_id=user_id,
            status=status,
            from_date=from_date,
            to_date=to_date,
        )
