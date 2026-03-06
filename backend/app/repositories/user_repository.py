"""User repository for database access."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Repository for user database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get a user by ID.

        Args:
            user_id: The user's UUID.

        Returns:
            The user if found, None otherwise.
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.session.scalar(stmt)
        return result

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email address.

        Args:
            email: The user's email address.

        Returns:
            The user if found, None otherwise.
        """
        stmt = select(User).where(User.email == email)
        result = await self.session.scalar(stmt)
        return result

    async def create(self, email: str, hashed_password: str) -> User:
        """Create a new user.

        Args:
            email: The user's email address.
            hashed_password: The hashed password.

        Returns:
            The created user.
        """
        user = User(email=email, hashed_password=hashed_password)
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(self, user: User) -> User:
        """Update a user.

        Args:
            user: The user to update.

        Returns:
            The updated user.
        """
        await self.session.flush()
        return user
