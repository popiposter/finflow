"""Telegram integration API routes."""

from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.schemas.telegram import TelegramUpdate, TelegramWebhookResponse
from app.services.telegram_bot_service import TelegramBotService

router = APIRouter(prefix="/integrations/telegram", tags=["telegram"])


async def get_telegram_bot_service() -> AsyncGenerator[TelegramBotService, None]:
    """Get Telegram bot service with a managed DB session."""
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            yield TelegramBotService(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@router.post(
    "/webhook/{webhook_secret}",
    response_model=TelegramWebhookResponse,
)
async def telegram_webhook(
    webhook_secret: str,
    update: TelegramUpdate,
    service: TelegramBotService = Depends(get_telegram_bot_service),
) -> TelegramWebhookResponse:
    """Receive Telegram webhook updates and turn plain text into transactions."""
    if not settings.telegram_bot_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "telegram_not_configured",
                "message": "Telegram bot token is not configured",
            },
        )

    if webhook_secret != settings.telegram_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    await service.handle_update(update)
    return TelegramWebhookResponse()
