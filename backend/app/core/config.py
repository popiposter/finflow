"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Annotated

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_title: str = "FinFlow Backend"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: Annotated[str, "PostgreSQL connection URL"] = (
        "postgresql+asyncpg://finflow:finflow@localhost:5432/finflow"
    )

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # API tokens (for iOS Shortcuts)
    api_token_length: int = 32
    api_token_expire_days: int = 365

    # Ollama LLM fallback parsing
    ollama_parse_enabled: bool = False
    ollama_api_base_url: str = "https://ollama.com/api"
    ollama_api_key: str | None = None
    ollama_model: str = "gpt-oss:120b"
    ollama_timeout_seconds: float = 20.0
    ollama_parse_min_confidence: float = 0.75

    # Telegram bot integration
    telegram_bot_token: str | None = None
    telegram_webhook_secret: str = "change-me-telegram-webhook-secret"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
