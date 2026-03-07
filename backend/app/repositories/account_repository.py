"""Account repository for database access."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.types import AccountType


class AccountRepository:
    """Repository for account database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.session = session

    async def get_by_id(self, account_id: UUID) -> Account | None:
        """Get an account by ID.

        Args:
            account_id: The account's UUID.

        Returns:
            The account if found, None otherwise.
        """
        stmt = select(Account).where(Account.id == account_id)
        result = await self.session.scalar(stmt)
        return result

    async def get_by_user(self, user_id: UUID) -> list[Account]:
        """Get all accounts for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            List of accounts for the user.
        """
        stmt = select(Account).where(Account.user_id == user_id)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def create(self, user_id: UUID, name: str, type_: AccountType) -> Account:
        """Create a new account.

        Args:
            user_id: The user's UUID.
            name: The account name.
            type_: The account type.

        Returns:
            The created account.
        """
        account = Account(user_id=user_id, name=name, type=type_)
        self.session.add(account)
        await self.session.flush()
        return account

    async def update(self, account: Account) -> Account:
        """Update an account.

        Args:
            account: The account to update.

        Returns:
            The updated account.
        """
        await self.session.flush()
        return account

    async def delete(self, account: Account) -> None:
        """Delete an account.

        Args:
            account: The account to delete.
        """
        await self.session.delete(account)
        await self.session.flush()
