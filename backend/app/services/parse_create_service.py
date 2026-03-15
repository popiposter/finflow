"""Transaction creation service for parse-and-create workflow."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.types import CategoryType, TransactionType
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.parse_create import ParseAndCreateResponse, ParsedResult
from app.services.llm_parse_service import LLMParseService
from app.services.parse_service import parse_text


class TransactionParseCreateService:
    """Service for creating transactions from parsed free-form text."""

    def __init__(
        self,
        session: AsyncSession,
        llm_parse_service: LLMParseService | None = None,
    ):
        """Initialize the service with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.session = session
        self.account_repo = AccountRepository(session)
        self.category_repo = CategoryRepository(session)
        self.transaction_repo = TransactionRepository(session)
        self.llm_parse_service = llm_parse_service or LLMParseService()

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
        parsed = await self._parse_with_fallback(text)

        if parsed.amount is None:
            raise ValueError("Could not extract amount from text")

        account = await self.account_repo.get_by_id(account_id)
        if account is None or account.user_id != user_id:
            raise ValueError("Account not found")

        resolved_category_id = category_id
        if resolved_category_id is not None:
            category = await self.category_repo.get_by_id(resolved_category_id)
            if category is None or category.user_id != user_id:
                raise ValueError("Category not found")
            if (
                parsed.transaction_type == TransactionType.EXPENSE
                and category.type == CategoryType.INCOME
            ):
                parsed.transaction_type = TransactionType.INCOME
        elif parsed.category_name is not None:
            category = await self.category_repo.get_by_user_and_name(
                user_id=user_id,
                name=parsed.category_name,
            )
            if category is not None:
                resolved_category_id = category.id
                if parsed.transaction_type == TransactionType.EXPENSE:
                    parsed.transaction_type = (
                        TransactionType.INCOME
                        if category.type == CategoryType.INCOME
                        else TransactionType.EXPENSE
                    )

        now = datetime.now(timezone.utc)
        transaction = await self.transaction_repo.create(
            user_id=user_id,
            account_id=account_id,
            amount=parsed.amount,
            type_=parsed.transaction_type,
            date_accrual=now,
            date_cash=now,
            category_id=resolved_category_id,
            description=parsed.description or parsed.original_text,
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
        return await self._parse_with_fallback(text)

    async def _parse_with_fallback(self, text: str) -> ParsedResult:
        parsed = parse_text(text)
        if parsed.amount is not None:
            return parsed

        llm_parsed = await self.llm_parse_service.parse_text(text)
        if llm_parsed is not None:
            return llm_parsed

        return parsed


__all__ = ["TransactionParseCreateService"]
