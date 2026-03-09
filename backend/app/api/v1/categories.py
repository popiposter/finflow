"""Category API routes."""

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

    Raises:
        HTTPException 400: If validation fails.
        HTTPException 404: If parent category not found or not owned by user.
    """
    # Validate parent category if specified
    if category_data.parent_id is not None:
        parent = await repo.get_by_id(category_data.parent_id)
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found",
            )
        # Parent must belong to same user (or be system-level)
        if parent.user_id is not None and parent.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found",
            )

    category = await repo.create(
        user_id=current_user.id,
        name=category_data.name,
        type_=category_data.type,
        parent_id=category_data.parent_id,
        display_order=category_data.display_order,
    )

    # Update optional fields
    if category_data.description is not None:
        category.description = category_data.description
    if category_data.is_active is not None:
        category.is_active = category_data.is_active

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
        List of categories owned by the user.
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


@router.put(
    "/{category_id}",
    response_model=CategoryOut,
)
async def update_category(
    category_id: str,
    category_data: CategoryCreate,
    current_user: UserOut = Depends(get_current_user),
    repo: CategoryRepository = Depends(get_category_repo),
) -> CategoryOut:
    """Update a category.

    Args:
        category_id: The category's UUID (as string).
        category_data: Category update data.
        current_user: Authenticated user.
        repo: Category repository dependency.

    Returns:
        Updated category.

    Raises:
        HTTPException 404: If category or parent category not found.
    """
    from uuid import UUID

    category_id_uuid = UUID(category_id)
    category = await repo.get_by_id(category_id_uuid)

    if category is None or category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Validate parent category if specified
    if category_data.parent_id is not None:
        parent = await repo.get_by_id(category_data.parent_id)
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found",
            )
        # Parent must belong to same user (or be system-level)
        if parent.user_id is not None and parent.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found",
            )

    # Update fields
    category.name = category_data.name
    category.type = category_data.type
    category.parent_id = category_data.parent_id
    if category_data.description is not None:
        category.description = category_data.description
    if category_data.is_active is not None:
        category.is_active = category_data.is_active
    if category_data.display_order is not None:
        category.display_order = category_data.display_order

    await repo.update(category)
    return CategoryOut.model_validate(category)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_category(
    category_id: str,
    current_user: UserOut = Depends(get_current_user),
    repo: CategoryRepository = Depends(get_category_repo),
) -> None:
    """Delete a category.

    Args:
        category_id: The category's UUID (as string).
        current_user: Authenticated user.
        repo: Category repository dependency.

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

    await repo.delete(category)


__all__ = ["router"]
