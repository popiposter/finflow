"""Category repository for database access."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.types import CategoryType


class CategoryRepository:
    """Repository for category database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session.

        Args:
            session: The async SQLAlchemy session.
        """
        self.session = session

    async def get_by_id(self, category_id: UUID) -> Category | None:
        """Get a category by ID.

        Args:
            category_id: The category's UUID.

        Returns:
            The category if found, None otherwise.
        """
        stmt = select(Category).where(Category.id == category_id)
        result = await self.session.scalar(stmt)
        return result

    async def get_by_user(self, user_id: UUID) -> list[Category]:
        """Get all categories for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            List of categories for the user.
        """
        stmt = select(Category).where(Category.user_id == user_id)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_by_type(self, user_id: UUID, type_: CategoryType) -> list[Category]:
        """Get categories by type for a user.

        Args:
            user_id: The user's UUID.
            type_: The category type (income/expense).

        Returns:
            List of categories of the specified type.
        """
        stmt = select(Category).where(
            Category.user_id == user_id,
            Category.type == type_,
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_children(self, parent_id: UUID) -> list[Category]:
        """Get child categories for a parent.

        Args:
            parent_id: The parent category's UUID.

        Returns:
            List of child categories.
        """
        stmt = select(Category).where(Category.parent_id == parent_id)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def create(
        self,
        user_id: UUID,
        name: str,
        type_: CategoryType,
        parent_id: UUID | None = None,
        display_order: int = 0,
    ) -> Category:
        """Create a new category.

        Args:
            user_id: The user's UUID.
            name: The category name.
            type_: The category type (income/expense).
            parent_id: Optional parent category ID for hierarchy.
            display_order: Display order within parent.

        Returns:
            The created category.
        """
        category = Category(
            user_id=user_id,
            name=name,
            type=type_,
            parent_id=parent_id,
            display_order=display_order,
        )
        self.session.add(category)
        await self.session.flush()
        return category

    async def update(self, category: Category) -> Category:
        """Update a category.

        Args:
            category: The category to update.

        Returns:
            The updated category.
        """
        await self.session.flush()
        return category

    async def delete(self, category: Category) -> None:
        """Delete a category.

        Args:
            category: The category to delete.
        """
        await self.session.delete(category)
        await self.session.flush()
