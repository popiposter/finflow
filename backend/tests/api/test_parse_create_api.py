"""API tests for parse-and-create transaction ingestion."""

from uuid import UUID

import pytest
from httpx import AsyncClient

from app.db import async_session_factory
from app.models.types import AccountType, CategoryType
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository

pytestmark = pytest.mark.api


def _error_message(response: AsyncClient | object) -> str:
    data = response.json()
    return data["error"]["message"]


async def _register_and_login(async_client: AsyncClient, email: str) -> tuple[str, str]:
    """Create a user and return (user_id, access_token)."""
    password = "SecurePass123!"
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    return register_response.json()["id"], login_response.json()["access_token"]


class TestParseCreateAPI:
    """Tests for POST /api/v1/transactions/parse-and-create."""

    async def test_parse_and_create_requires_auth(self, async_client: AsyncClient) -> None:
        """The endpoint should require bearer auth."""
        response = await async_client.post(
            "/api/v1/transactions/parse-and-create",
            json={"text": "кофе 300", "account_id": "12345678-1234-1234-1234-123456789012"},
        )

        assert response.status_code == 401

    async def test_parse_and_create_requires_account_id(
        self, async_client: AsyncClient
    ) -> None:
        """Explicit account selection remains mandatory."""
        _, access_token = await _register_and_login(
            async_client, "parse-no-account@example.com"
        )

        response = await async_client.post(
            "/api/v1/transactions/parse-and-create",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"text": "кофе 300"},
        )

        assert response.status_code == 400
        assert "account_id is required" in _error_message(response)

    async def test_parse_and_create_persists_income_with_detected_category(
        self, async_client: AsyncClient
    ) -> None:
        """Parser should auto-match user category and persist income type."""
        user_id, access_token = await _register_and_login(
            async_client, "parse-income@example.com"
        )

        async with async_session_factory() as session:
            account_repo = AccountRepository(session)
            account = await account_repo.create(
                user_id=user_id,
                name="Main account",
                type_=AccountType.CHECKING,
            )
            category_repo = CategoryRepository(session)
            income_category = await category_repo.create(
                user_id=user_id,
                name="Доход",
                type_=CategoryType.INCOME,
            )
            await session.commit()

        response = await async_client.post(
            "/api/v1/transactions/parse-and-create",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "text": "зарплата 120000",
                "account_id": str(account.id),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == "120000.00"
        assert data["type"] == "income"
        assert data["category_id"] == str(income_category.id)
        assert data["description"] == "зарплата"

        async with async_session_factory() as session:
            transaction_repo = TransactionRepository(session)
            transactions = await transaction_repo.get_by_user(UUID(user_id))
            assert len(transactions) == 1
            assert transactions[0].type == "income"

    async def test_parse_and_create_prefers_money_amount_in_multiple_numbers(
        self, async_client: AsyncClient
    ) -> None:
        """Money marker should win when text contains multiple numeric tokens."""
        user_id, access_token = await _register_and_login(
            async_client, "parse-multi@example.com"
        )

        async with async_session_factory() as session:
            account_repo = AccountRepository(session)
            account = await account_repo.create(
                user_id=user_id,
                name="Main account",
                type_=AccountType.CHECKING,
            )
            category_repo = CategoryRepository(session)
            await category_repo.create(
                user_id=user_id,
                name="Продукты",
                type_=CategoryType.EXPENSE,
            )
            await session.commit()

        response = await async_client.post(
            "/api/v1/transactions/parse-and-create",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "text": "покупки 1500 и 300 рублей",
                "account_id": str(account.id),
            },
        )

        assert response.status_code == 200
        assert response.json()["amount"] == "300.00"

    async def test_parse_and_create_rejects_foreign_account(
        self, async_client: AsyncClient
    ) -> None:
        """A user should not be able to create into another user's account."""
        _, access_token = await _register_and_login(
            async_client, "parse-owner@example.com"
        )
        foreign_user_id, _ = await _register_and_login(
            async_client, "parse-foreign@example.com"
        )

        async with async_session_factory() as session:
            account_repo = AccountRepository(session)
            foreign_account = await account_repo.create(
                user_id=foreign_user_id,
                name="Foreign account",
                type_=AccountType.CHECKING,
            )
            await session.commit()

        response = await async_client.post(
            "/api/v1/transactions/parse-and-create",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "text": "кофе 300",
                "account_id": str(foreign_account.id),
            },
        )

        assert response.status_code == 400
        assert _error_message(response) == "Account not found"
