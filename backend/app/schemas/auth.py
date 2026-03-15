"""Authentication schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str


class UserOut(UserBase):
    """Schema for user responses."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for token responses."""

    access_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for token refresh response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Schema for login request."""

    email: EmailStr
    password: str


class ApiTokenCreate(BaseModel):
    """Schema for API token creation."""

    name: str


class ApiTokenOut(BaseModel):
    """Schema for API token response (stored data)."""

    id: UUID
    user_id: UUID
    name: str
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime
    is_revoked: bool

    model_config = {"from_attributes": True}


class ApiTokenOutWithToken(ApiTokenOut):
    """Schema for API token response including the raw token.

    This schema is used only for the initial creation response
    when the raw token should be shown once to the user.
    """

    raw_token: str


class TelegramChatLinkOut(BaseModel):
    """Schema for Telegram chat link responses."""

    id: UUID
    user_id: UUID
    account_id: UUID
    chat_id: int
    telegram_user_id: int | None
    username: str | None
    first_name: str | None
    is_active: bool
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TelegramChatLinkUpdate(BaseModel):
    """Schema for changing the default account on a linked Telegram chat."""

    account_id: UUID


class TelegramIntegrationStatus(BaseModel):
    """Public runtime status for Telegram integration."""

    enabled: bool
    bot_token_configured: bool
    webhook_secret_configured: bool
    commands: list[str]


class OllamaIntegrationStatus(BaseModel):
    """Public runtime status for Ollama-backed parsing."""

    enabled: bool
    api_key_configured: bool
    base_url: str
    model: str
    min_confidence: float


class IntegrationStatusResponse(BaseModel):
    """Public runtime status for supported integrations."""

    telegram: TelegramIntegrationStatus
    ollama: OllamaIntegrationStatus
