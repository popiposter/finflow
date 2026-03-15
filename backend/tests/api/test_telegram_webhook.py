"""API tests for Telegram bot webhook ingestion."""

from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.db.session import async_session_factory
from app.models.types import AccountType
from app.repositories.account_repository import AccountRepository
from app.services.telegram_bot_service import TelegramBotService

pytestmark = pytest.mark.api


async def _register_login_and_create_account(
    async_client: AsyncClient,
    *,
    email: str,
) -> tuple[str, str]:
    register = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass123!"},
    )
    assert register.status_code == 201
    user_id = register.json()["id"]

    login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass123!"},
    )
    assert login.status_code == 200
    access_token = login.json()["access_token"]

    async with async_session_factory() as session:
        account_repo = AccountRepository(session)
        account = await account_repo.create(
            user_id=user_id,
            name="Main Cash",
            type_=AccountType.CHECKING,
        )
        await session.commit()
        return access_token, str(account.id)


class TestTelegramWebhook:
    async def test_connect_and_create_transaction(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(settings, "telegram_bot_token", "test-bot-token")
        monkeypatch.setattr(settings, "telegram_webhook_secret", "test-secret")

        replies: list[tuple[int, str]] = []

        async def fake_send_message(
            self: TelegramBotService,
            chat_id: int,
            text: str,
        ) -> None:
            replies.append((chat_id, text))

        monkeypatch.setattr(TelegramBotService, "_send_message", fake_send_message)

        access_token, account_id = await _register_login_and_create_account(
            async_client,
            email="telegram@example.com",
        )

        token_response = await async_client.post(
            "/api/v1/auth/api-tokens",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Telegram Bot"},
        )
        assert token_response.status_code == 200
        raw_token = token_response.json()["raw_token"]

        connect_response = await async_client.post(
            "/api/v1/integrations/telegram/webhook/test-secret",
            json={
                "update_id": 1,
                "message": {
                    "message_id": 10,
                    "text": f"/connect {raw_token} {account_id}",
                    "chat": {"id": 555001, "type": "private"},
                    "from": {
                        "id": 9001,
                        "username": "finflow_user",
                        "first_name": "Fin",
                    },
                },
            },
        )
        assert connect_response.status_code == 200
        assert replies[-1][0] == 555001
        assert "Telegram is now linked" in replies[-1][1]

        create_response = await async_client.post(
            "/api/v1/integrations/telegram/webhook/test-secret",
            json={
                "update_id": 2,
                "message": {
                    "message_id": 11,
                    "text": "кофе 350р",
                    "chat": {"id": 555001, "type": "private"},
                    "from": {
                        "id": 9001,
                        "username": "finflow_user",
                        "first_name": "Fin",
                    },
                },
            },
        )
        assert create_response.status_code == 200
        assert "Saved transaction" in replies[-1][1]

        transactions = await async_client.get(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert transactions.status_code == 200
        body = transactions.json()
        assert len(body) == 1
        assert "кофе" in body[0]["description"]
        assert Decimal(body[0]["amount"]) == Decimal("350")

    async def test_plain_text_requires_chat_link(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(settings, "telegram_bot_token", "test-bot-token")
        monkeypatch.setattr(settings, "telegram_webhook_secret", "test-secret")

        replies: list[str] = []

        async def fake_send_message(
            self: TelegramBotService,
            chat_id: int,
            text: str,
        ) -> None:
            del self, chat_id
            replies.append(text)

        monkeypatch.setattr(TelegramBotService, "_send_message", fake_send_message)

        response = await async_client.post(
            "/api/v1/integrations/telegram/webhook/test-secret",
            json={
                "update_id": 3,
                "message": {
                    "message_id": 22,
                    "text": "coffee 350",
                    "chat": {"id": 555002, "type": "private"},
                    "from": {"id": 9002, "username": "new_user", "first_name": "New"},
                },
            },
        )

        assert response.status_code == 200
        assert "Use /connect" in replies[-1]

    async def test_connect_rejects_invalid_api_token(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(settings, "telegram_bot_token", "test-bot-token")
        monkeypatch.setattr(settings, "telegram_webhook_secret", "test-secret")

        replies: list[str] = []

        async def fake_send_message(
            self: TelegramBotService,
            chat_id: int,
            text: str,
        ) -> None:
            del self, chat_id
            replies.append(text)

        monkeypatch.setattr(TelegramBotService, "_send_message", fake_send_message)

        response = await async_client.post(
            "/api/v1/integrations/telegram/webhook/test-secret",
            json={
                "update_id": 4,
                "message": {
                    "message_id": 23,
                    "text": "/connect definitely-not-a-real-token",
                    "chat": {"id": 555003, "type": "private"},
                    "from": {"id": 9003, "username": "broken", "first_name": "Bad"},
                },
            },
        )

        assert response.status_code == 200
        assert "Could not verify that API token" in replies[-1]
