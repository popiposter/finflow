"""Test configuration and fixtures for backend tests."""

from collections.abc import AsyncGenerator, Generator
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import TestClient

import app.models  # noqa: F401
from app.db import Base, async_session_factory, engine
from app.main import app
from app.models.account import Account
from app.models.category import Category
from app.models.user import User
from app.models.types import AccountType, CategoryType


@pytest.fixture
def client(prepare_database: None) -> Generator[TestClient, None, None]:
    """Create a synchronous test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def prepare_database() -> AsyncGenerator[None, None]:
    """Create database tables for an individual test and drop them afterwards.

    The async engine is disposed before and after each test so pooled
    asyncpg connections never leak across pytest event loops.
    """
    await engine.dispose()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def clean_db(prepare_database: None) -> AsyncGenerator[None, None]:
    """Provide a compatibility fixture for DB-backed tests.

    Database isolation is handled by the per-test schema lifecycle in
    ``prepare_database``.
    """
    yield


@pytest_asyncio.fixture
async def db_session(prepare_database: None) -> AsyncGenerator[AsyncSession, None]:
    """Create an async database session for a test."""
    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def user_with_account_category(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> AsyncGenerator[dict, None]:
    """Create a user, account, and category for planned payment tests.

    This fixture registers a user via API, then creates an account and category
    directly in the database using the user's ID from the registration response.

    Returns:
        Dict with user_id, account_id, category_id, and access_token.
    """
    # Register user via API
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "ppuser@example.com", "password": "SecurePass123!"},
    )
    assert register_response.status_code == 201
    user_data = register_response.json()
    user_id = user_data["id"]

    # Create account directly in DB
    from app.models.types import AccountType, CategoryType
    from app.repositories.account_repository import AccountRepository
    from app.repositories.category_repository import CategoryRepository

    account_repo = AccountRepository(db_session)
    account = await account_repo.create(
        user_id=user_id,
        name="Test Account",
        type_=AccountType.CHECKING,
    )
    account.currency_code = "USD"
    account.current_balance = Decimal("0.00")
    await account_repo.update(account)

    category_repo = CategoryRepository(db_session)
    category = await category_repo.create(
        user_id=user_id,
        name="Housing",
        type_=CategoryType.EXPENSE,
    )

    await db_session.commit()

    # Login to get access token
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "ppuser@example.com", "password": "SecurePass123!"},
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    yield {
        "user_id": user_id,
        "account_id": account.id,
        "category_id": category.id,
        "access_token": access_token,
    }

    # Cleanup
    await db_session.delete(category)
    await db_session.delete(account)
    await db_session.commit()


@pytest_asyncio.fixture
async def async_client(prepare_database: None) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for API tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver.local",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def test_account(
    db_session: AsyncSession,
) -> AsyncGenerator[Account, None]:
    """Create a test account for planned payment tests."""
    user_id = uuid4()
    account = Account(
        user_id=user_id,
        name="Test Checking Account",
        type=AccountType.CHECKING,
        currency_code="USD",
        current_balance=Decimal("0.00"),
    )
    db_session.add(account)
    await db_session.flush()
    await db_session.refresh(account)
    yield account
    await db_session.delete(account)
    await db_session.commit()


@pytest_asyncio.fixture
async def test_account_with_user(
    db_session: AsyncSession,
) -> AsyncGenerator[tuple[UUID, Account], None]:
    """Create a test account with user_id for planned payment tests.

    Returns:
        Tuple of (user_id, account).
    """
    user_id = uuid4()
    user = User(
        id=user_id,
        email=f"{user_id}@example.com",
        hashed_password="test-hash",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    account = Account(
        user_id=user_id,
        name="Test Checking Account",
        type=AccountType.CHECKING,
        currency_code="USD",
        current_balance=Decimal("0.00"),
    )
    db_session.add(account)
    await db_session.flush()
    await db_session.refresh(account)
    yield user_id, account
    await db_session.delete(account)
    await db_session.delete(user)
    await db_session.commit()


@pytest_asyncio.fixture
async def test_category(
    db_session: AsyncSession,
) -> AsyncGenerator[Category, None]:
    """Create a test category for planned payment tests."""
    user_id = uuid4()
    category = Category(
        user_id=user_id,
        name="Housing",
        type=CategoryType.EXPENSE,
    )
    db_session.add(category)
    await db_session.flush()
    await db_session.refresh(category)
    yield category
    await db_session.delete(category)
    await db_session.commit()


@pytest_asyncio.fixture
async def test_category_with_user(
    db_session: AsyncSession,
) -> AsyncGenerator[tuple[Category, uuid4.__class__], None]:
    """Create a test category with user_id for planned payment tests.

    Returns:
        Tuple of (category, user_id).
    """
    user_id = uuid4()
    category = Category(
        user_id=user_id,
        name="Housing",
        type=CategoryType.EXPENSE,
    )
    db_session.add(category)
    await db_session.flush()
    await db_session.refresh(category)
    yield category, user_id
    await db_session.delete(category)
    await db_session.commit()
