"""API tests for request IDs and rate limiting."""

import pytest
from httpx import AsyncClient

from app.core.config import settings

pytestmark = pytest.mark.api


async def test_login_rate_limit_returns_429(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Login should be rate-limited after repeated failures."""
    monkeypatch.setattr(settings, "auth_rate_limit_requests", 2)
    monkeypatch.setattr(settings, "auth_rate_limit_window_seconds", 60)

    for _ in range(2):
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "missing@example.com", "password": "wrong"},
        )
        assert response.status_code == 401

    limited = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "wrong"},
    )

    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "rate_limited"


async def test_parse_and_create_rate_limit_returns_429(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Parse-and-create should be rate-limited per caller."""
    monkeypatch.setattr(settings, "parse_rate_limit_requests", 1)
    monkeypatch.setattr(settings, "parse_rate_limit_window_seconds", 60)

    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "parse-limit@example.com", "password": "SecurePass123!"},
    )
    login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "parse-limit@example.com", "password": "SecurePass123!"},
    )
    access_token = login.json()["access_token"]

    first = await async_client.post(
        "/api/v1/transactions/parse-and-create",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "text": "coffee 350",
            "account_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert first.status_code in {400, 404}

    second = await async_client.post(
        "/api/v1/transactions/parse-and-create",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "text": "coffee 350",
            "account_id": "00000000-0000-0000-0000-000000000000",
        },
    )

    assert second.status_code == 429
    assert second.json()["error"]["code"] == "rate_limited"


async def test_telegram_webhook_rate_limit_returns_429(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Telegram webhook should be rate-limited before business logic runs."""
    monkeypatch.setattr(settings, "telegram_bot_token", "test-bot-token")
    monkeypatch.setattr(settings, "telegram_webhook_secret", "test-secret")
    monkeypatch.setattr(settings, "telegram_rate_limit_requests", 1)
    monkeypatch.setattr(settings, "telegram_rate_limit_window_seconds", 60)

    first = await async_client.post(
        "/api/v1/integrations/telegram/webhook/test-secret",
        json={
            "update_id": 1,
            "message": {
                "message_id": 10,
                "text": "/status",
                "chat": {"id": 999001, "type": "private"},
                "from": {"id": 9001, "username": "tester", "first_name": "Test"},
            },
        },
    )
    assert first.status_code == 200

    second = await async_client.post(
        "/api/v1/integrations/telegram/webhook/test-secret",
        json={
            "update_id": 2,
            "message": {
                "message_id": 11,
                "text": "/status",
                "chat": {"id": 999001, "type": "private"},
                "from": {"id": 9001, "username": "tester", "first_name": "Test"},
            },
        },
    )

    assert second.status_code == 429
    assert second.json()["error"]["code"] == "rate_limited"
