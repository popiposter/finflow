"""Health check endpoints."""

from typing import cast

from fastapi import APIRouter, Request

from app.core.config import settings
from app.schemas.auth import IntegrationStatusResponse, OllamaIntegrationStatus, TelegramIntegrationStatus

router = APIRouter()


@router.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Return health status."""
    return {
        "status": "healthy",
        "app": settings.app_title,
        "version": settings.app_version,
    }


@router.get("/health/scheduler", tags=["system"])
async def scheduler_health_check(request: Request) -> dict[str, str | None]:
    """Return scheduler status."""
    scheduler_manager = request.app.state.scheduler_manager
    return cast(dict[str, str | None], scheduler_manager.health())


@router.get("/health/integrations", tags=["system"], response_model=IntegrationStatusResponse)
async def integrations_health_check() -> IntegrationStatusResponse:
    """Return safe public runtime status for optional integrations."""
    telegram = TelegramIntegrationStatus(
        enabled=bool(settings.telegram_bot_token and settings.telegram_webhook_secret),
        bot_token_configured=bool(settings.telegram_bot_token),
        webhook_secret_configured=bool(settings.telegram_webhook_secret),
        commands=["/connect <api_token> [account_id]", "/status", "/disconnect"],
    )
    ollama = OllamaIntegrationStatus(
        enabled=settings.ollama_parse_enabled,
        api_key_configured=bool(settings.ollama_api_key),
        base_url=settings.ollama_api_base_url,
        model=settings.ollama_model,
        min_confidence=settings.ollama_parse_min_confidence,
    )
    return IntegrationStatusResponse(telegram=telegram, ollama=ollama)
