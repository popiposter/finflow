"""Schemas for Telegram webhook handling."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TelegramUser(BaseModel):
    """Telegram sender identity."""

    id: int
    username: str | None = None
    first_name: str | None = None


class TelegramChat(BaseModel):
    """Telegram chat metadata."""

    id: int
    type: str


class TelegramMessage(BaseModel):
    """Telegram inbound message payload."""

    message_id: int
    chat: TelegramChat
    text: str | None = None
    from_user: TelegramUser | None = Field(default=None, alias="from")


class TelegramUpdate(BaseModel):
    """Telegram webhook update."""

    update_id: int
    message: TelegramMessage | None = None


class TelegramWebhookResponse(BaseModel):
    """Acknowledgement response for Telegram webhooks."""

    ok: bool = True
