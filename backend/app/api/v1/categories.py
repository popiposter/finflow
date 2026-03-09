"""Categories API routes."""

from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import get_current_user
from app.repositories.category_repository import CategoryRepository
from app.schemas.auth import UserOut
from app.schemas.finance import CategoryCreate, CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"])


async def get_category_repo(
    user: UserOut = Depends(get_current_user),
) -> AsyncGenerator[CategoryRepository, None]:
    """Get category repository with database session.

    Args:
        user: Current authenticated user.

    Yields:
        CategoryRepository instance.
    """
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            yield CategoryRepository(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@router.post(
    "",
    response_model=CategoryOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    category_data: CategoryCreate,
    current_user: UserOut = Depends(get_current_user),
    repo: CategoryRepository = Depends(get_category_repo),
) -> CategoryOut:
    """Create a new category.

    Args:
        category_data: Category creation data.
        current_user: Authenticated user.
        repo: Category repository dependency.

    Returns:
        Created category.
    """
    category = await repo.create(
        user_id=current_user.id,
        name=category_data.name,
        type_=category_data.type,
    )

    # Update remaining fields
    category.description = category_data.description
    category.parent_id = category_data.parent_id
    category.is_active = category_data.is_active
    category.display_order = category_data.display_order

    await repo.update(category)
    return CategoryOut.model_validate(category)


@router.get(
    "",
    response_model=list[CategoryOut],
)
async def list_categories(
    current_user: UserOut = Depends(get_current_user),
    repo: CategoryRepository = Depends(get_category_repo),
) -> list[CategoryOut]:
    """List all categories for the current user.

    Args:
        current_user: Authenticated user.
        repo: Category repository dependency.

    Returns:
        List of categories.
    """
    categories = await repo.get_by_user(current_user.id)
    return [CategoryOut.model_validate(c) for c in categories]


@router.get(
    "/{category_id}",
    response_model=CategoryOut,
)
async def get_category(
    category_id: str,
    current_user: UserOut = Depends(get_current_user),
    repo: CategoryRepository = Depends(get_category_repo),
) -> CategoryOut:
    """Get a specific category by ID.

    Args:
        category_id: The category's UUID (as string).
        current_user: Authenticated user.
        repo: Category repository dependency.

    Returns:
        The category.

    Raises:
        HTTPException 404: If category not found or not owned by user.
    """
    from uuid import UUID

    category_id_uuid = UUID(category_id)
    category = await repo.get_by_id(category_id_uuid)

    if category is None or category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return CategoryOut.model_validate(category)
