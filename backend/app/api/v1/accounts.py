"""Accounts API routes."""

from decimal import Decimal
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import get_current_user
from app.repositories.account_repository import AccountRepository
from app.schemas.auth import UserOut
from app.schemas.finance import AccountCreate, AccountOut

router = APIRouter(prefix="/accounts", tags=["accounts"])


async def get_account_repo(
    user: UserOut = Depends(get_current_user),
) -> AsyncGenerator[AccountRepository, None]:
    """Get account repository with database session.

    Args:
        user: Current authenticated user.

    Yields:
        AccountRepository instance.
    """
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            yield AccountRepository(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@router.post(
    "",
    response_model=AccountOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_account(
    account_data: AccountCreate,
    current_user: UserOut = Depends(get_current_user),
    repo: AccountRepository = Depends(get_account_repo),
) -> AccountOut:
    """Create a new account.

    Args:
        account_data: Account creation data.
        current_user: Authenticated user.
        repo: Account repository dependency.

    Returns:
        Created account.
    """
    account = await repo.create(
        user_id=current_user.id,
        name=account_data.name,
        type_=account_data.type,
    )

    # Update remaining fields
    account.description = account_data.description
    account.currency_code = account_data.currency_code
    account.is_active = account_data.is_active
    balance = account_data.current_balance or Decimal("0.00")
    account.current_balance = balance  # type: ignore[assignment]

    await repo.update(account)
    return AccountOut.model_validate(account)


@router.get(
    "",
    response_model=list[AccountOut],
)
async def list_accounts(
    current_user: UserOut = Depends(get_current_user),
    repo: AccountRepository = Depends(get_account_repo),
) -> list[AccountOut]:
    """List all accounts for the current user.

    Args:
        current_user: Authenticated user.
        repo: Account repository dependency.

    Returns:
        List of accounts.
    """
    accounts = await repo.get_by_user(current_user.id)
    return [AccountOut.model_validate(a) for a in accounts]


@router.get(
    "/{account_id}",
    response_model=AccountOut,
)
async def get_account(
    account_id: str,
    current_user: UserOut = Depends(get_current_user),
    repo: AccountRepository = Depends(get_account_repo),
) -> AccountOut:
    """Get a specific account by ID.

    Args:
        account_id: The account's UUID (as string).
        current_user: Authenticated user.
        repo: Account repository dependency.

    Returns:
        The account.

    Raises:
        HTTPException 404: If account not found or not owned by user.
    """
    from uuid import UUID

    account_id_uuid = UUID(account_id)
    account = await repo.get_by_id(account_id_uuid)

    if account is None or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    return AccountOut.model_validate(account)
