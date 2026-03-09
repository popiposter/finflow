"""Transaction API routes."""

from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import get_current_user
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.auth import UserOut
from app.schemas.finance import TransactionCreate, TransactionOut
from app.schemas.parse_create import (
    ParseAndCreateResponse,
    ParseErrorResponse,
    ParseRequest,
)
from app.services.parse_create_service import TransactionParseCreateService

router = APIRouter(prefix="/transactions", tags=["transactions"])


async def get_parse_create_service() -> AsyncGenerator[
    TransactionParseCreateService, None
]:
    """Get parse-create service with database session.

    Yields:
        TransactionParseCreateService instance.
    """
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            yield TransactionParseCreateService(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_transaction_repo(
    user: UserOut = Depends(get_current_user),
) -> AsyncGenerator[TransactionRepository, None]:
    """Get transaction repository with database session.

    Args:
        user: Current authenticated user.

    Yields:
        TransactionRepository instance.
    """
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            yield TransactionRepository(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


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
    "/parse-and-create",
    response_model=ParseAndCreateResponse,
    responses={
        400: {"model": ParseErrorResponse, "description": "Invalid request"},
        401: {"description": "Not authenticated"},
    },
)
async def parse_and_create(
    request: ParseRequest,
    current_user: UserOut = Depends(get_current_user),
    service: TransactionParseCreateService = Depends(get_parse_create_service),
) -> ParseAndCreateResponse:
    """Parse free-form text and create a transaction.

    Accepts free-form text from iOS Shortcut and creates a transaction
    in the database.

    Args:
        request: ParseRequest with free-form text and target account.
        current_user: Authenticated user.
        service: Parse-create service dependency.

    Returns:
        ParseAndCreateResponse with created transaction details.

    Raises:
        HTTPException 400: If amount cannot be extracted or account is missing.
        HTTPException 401: If not authenticated.
    """
    if request.account_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="account_id is required until default account selection is implemented",
        )

    try:
        return await service.parse_and_create(
            text=request.text,
            user_id=current_user.id,
            account_id=request.account_id,
            category_id=request.category_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post(
    "",
    response_model=TransactionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: UserOut = Depends(get_current_user),
    repo: TransactionRepository = Depends(get_transaction_repo),
    account_repo: AccountRepository = Depends(get_account_repo),
    category_repo: CategoryRepository = Depends(get_category_repo),
) -> TransactionOut:
    """Create a new transaction.

    Args:
        transaction_data: Transaction creation data.
        current_user: Authenticated user.
        repo: Transaction repository dependency.
        account_repo: Account repository dependency.
        category_repo: Category repository dependency.

    Returns:
        Created transaction.

    Raises:
        HTTPException 400: If validation fails.
        HTTPException 404: If account or category not found.
    """
    # Validate account belongs to user
    account = await account_repo.get_by_id(transaction_data.account_id)
    if account is None or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    # Validate category belongs to user if specified
    if transaction_data.category_id is not None:
        category = await category_repo.get_by_id(transaction_data.category_id)
        if category is None or category.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

    # Validate counterparty account belongs to user if specified
    if transaction_data.counterparty_account_id is not None:
        counterparty_account = await account_repo.get_by_id(
            transaction_data.counterparty_account_id
        )
        if (
            counterparty_account is None
            or counterparty_account.user_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Counterparty account not found",
            )

    transaction = await repo.create(
        user_id=current_user.id,
        account_id=transaction_data.account_id,
        amount=transaction_data.amount,
        type_=transaction_data.type,
        date_accrual=transaction_data.date_accrual,
        date_cash=transaction_data.date_cash,
        category_id=transaction_data.category_id,
        counterparty_account_id=transaction_data.counterparty_account_id,
        description=transaction_data.description,
        is_reconciled=transaction_data.is_reconciled,
    )

    return TransactionOut.model_validate(transaction)


@router.get(
    "",
    response_model=list[TransactionOut],
)
async def list_transactions(
    current_user: UserOut = Depends(get_current_user),
    repo: TransactionRepository = Depends(get_transaction_repo),
) -> list[TransactionOut]:
    """List all transactions for the current user.

    Args:
        current_user: Authenticated user.
        repo: Transaction repository dependency.

    Returns:
        List of transactions owned by the user.
    """
    transactions = await repo.get_by_user(current_user.id)
    return [TransactionOut.model_validate(t) for t in transactions]


@router.get(
    "/{transaction_id}",
    response_model=TransactionOut,
)
async def get_transaction(
    transaction_id: str,
    current_user: UserOut = Depends(get_current_user),
    repo: TransactionRepository = Depends(get_transaction_repo),
) -> TransactionOut:
    """Get a specific transaction by ID.

    Args:
        transaction_id: The transaction's UUID (as string).
        current_user: Authenticated user.
        repo: Transaction repository dependency.

    Returns:
        The transaction.

    Raises:
        HTTPException 404: If transaction not found or not owned by user.
    """
    transaction_id_uuid = UUID(transaction_id)
    transaction = await repo.get_by_id(transaction_id_uuid)

    if transaction is None or transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return TransactionOut.model_validate(transaction)


@router.put(
    "/{transaction_id}",
    response_model=TransactionOut,
)
async def update_transaction(
    transaction_id: str,
    transaction_data: TransactionCreate,
    current_user: UserOut = Depends(get_current_user),
    repo: TransactionRepository = Depends(get_transaction_repo),
    account_repo: AccountRepository = Depends(get_account_repo),
    category_repo: CategoryRepository = Depends(get_category_repo),
) -> TransactionOut:
    """Update a transaction.

    Args:
        transaction_id: The transaction's UUID (as string).
        transaction_data: Transaction update data.
        current_user: Authenticated user.
        repo: Transaction repository dependency.
        account_repo: Account repository dependency.
        category_repo: Category repository dependency.

    Returns:
        Updated transaction.

    Raises:
        HTTPException 404: If transaction not found or not owned by user.
    """
    transaction_id_uuid = UUID(transaction_id)
    transaction = await repo.get_by_id(transaction_id_uuid)

    if transaction is None or transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    # Validate account belongs to user
    account = await account_repo.get_by_id(transaction_data.account_id)
    if account is None or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    # Validate category belongs to user if specified
    if transaction_data.category_id is not None:
        category = await category_repo.get_by_id(transaction_data.category_id)
        if category is None or category.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

    # Validate counterparty account belongs to user if specified
    if transaction_data.counterparty_account_id is not None:
        counterparty_account = await account_repo.get_by_id(
            transaction_data.counterparty_account_id
        )
        if (
            counterparty_account is None
            or counterparty_account.user_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Counterparty account not found",
            )

    # Update fields
    transaction.account_id = transaction_data.account_id
    transaction.category_id = transaction_data.category_id
    transaction.counterparty_account_id = transaction_data.counterparty_account_id
    transaction.amount = transaction_data.amount
    transaction.type = transaction_data.type
    transaction.description = transaction_data.description
    transaction.date_accrual = transaction_data.date_accrual
    transaction.date_cash = transaction_data.date_cash
    transaction.is_reconciled = transaction_data.is_reconciled

    await repo.update(transaction)
    return TransactionOut.model_validate(transaction)


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_transaction(
    transaction_id: str,
    current_user: UserOut = Depends(get_current_user),
    repo: TransactionRepository = Depends(get_transaction_repo),
) -> None:
    """Delete a transaction.

    Args:
        transaction_id: The transaction's UUID (as string).
        current_user: Authenticated user.
        repo: Transaction repository dependency.

    Raises:
        HTTPException 404: If transaction not found or not owned by user.
    """
    transaction_id_uuid = UUID(transaction_id)
    transaction = await repo.get_by_id(transaction_id_uuid)

    if transaction is None or transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    await repo.delete(transaction)


__all__ = ["router"]
