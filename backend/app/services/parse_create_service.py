"""Transaction creation service for parse-and-create workflow."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.types import TransactionType
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.parse_create import ParseAndCreateResponse, ParsedResult
from app.services.parse_service import parse_text


class TransactionParseCreateService:
    """Service for creating transactions from parsed free-form text."""

    def __init__(self, session: AsyncSession):
        """Initialize the service with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.session = session
        self.transaction_repo = TransactionRepository(session)

    async def parse_and_create(
        self,
        text: str,
        user_id: UUID,
        account_id: UUID,
        category_id: UUID | None = None,
    ) -> ParseAndCreateResponse:
        """Parse free-form text and create a transaction.

        Args:
            text: Free-form text to parse (e.g., from iOS Shortcut).
            user_id: The authenticated user's UUID.
            account_id: Account ID for the transaction.
            category_id: Optional category ID.

        Returns:
            ParseAndCreateResponse with created transaction details.

        Raises:
            ValueError: If amount cannot be extracted from text.
        """
        parsed = parse_text(text)

        if parsed.amount is None:
            raise ValueError("Could not extract amount from text")

        now = datetime.now(timezone.utc)
        transaction = await self.transaction_repo.create(
            user_id=user_id,
            account_id=account_id,
            amount=parsed.amount,
            type_=TransactionType.EXPENSE,
            date_accrual=now,
            date_cash=now,
            category_id=category_id,
            description=parsed.original_text,
            is_reconciled=False,
        )

        return ParseAndCreateResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            account_id=transaction.account_id,
            category_id=transaction.category_id,
            amount=transaction.amount,
            type=transaction.type.value,
            description=transaction.description or "",
            date_accrual=transaction.date_accrual,
            date_cash=transaction.date_cash,
            is_reconciled=transaction.is_reconciled,
        )

    async def parse_only(self, text: str) -> ParsedResult:
        """Parse text without creating a transaction.

        Useful for previewing what would be created.

        Args:
            text: Free-form text to parse.

        Returns:
            ParsedResult with extracted fields.
        """
        return parse_text(text)


__all__ = ["TransactionParseCreateService"]
