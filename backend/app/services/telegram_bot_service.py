"""Telegram bot ingestion workflow."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password
from app.models.user import User
from app.repositories.account_repository import AccountRepository
from app.repositories.api_token_repository import ApiTokenRepository
from app.repositories.telegram_chat_link_repository import TelegramChatLinkRepository
from app.repositories.user_repository import UserRepository
from app.schemas.telegram import TelegramMessage, TelegramUpdate
from app.services.parse_create_service import TransactionParseCreateService

logger = logging.getLogger(__name__)


class TelegramBotService:
    """Handles Telegram bot webhook updates."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.account_repo = AccountRepository(session)
        self.api_token_repo = ApiTokenRepository(session)
        self.link_repo = TelegramChatLinkRepository(session)
        self.parse_create_service = TransactionParseCreateService(session)
        self.user_repo = UserRepository(session)

    async def handle_update(self, update: TelegramUpdate) -> None:
        """Process an incoming Telegram webhook update."""
        message = update.message
        if message is None or not message.text:
            return

        text = message.text.strip()
        if not text:
            return

        if text.startswith("/connect"):
            reply = await self._handle_connect(message)
        elif text.startswith("/status"):
            reply = await self._handle_status(message)
        elif text.startswith("/disconnect"):
            reply = await self._handle_disconnect(message)
        else:
            reply = await self._handle_transaction_text(message, text)

        await self._send_message(message.chat.id, reply)

    async def _handle_connect(self, message: TelegramMessage) -> str:
        parts = (message.text or "").split()
        if len(parts) < 2:
            return (
                "Usage: /connect <api_token> [account_id]\n"
                "If your FinFlow user has only one account, account_id is optional."
            )

        raw_token = parts[1].strip()
        account_id_arg = parts[2].strip() if len(parts) >= 3 else None

        user = await self._authenticate_api_token(raw_token)
        if user is None:
            return "Could not verify that API token. Create a fresh token in FinFlow and try again."

        accounts = await self.account_repo.get_by_user(user.id)
        if not accounts:
            return "No accounts are available for this FinFlow user yet. Create an account first."

        account_id: UUID | None = None
        if account_id_arg:
            try:
                account_id = UUID(account_id_arg)
            except ValueError:
                return "account_id must be a valid UUID."
        elif len(accounts) == 1:
            account_id = accounts[0].id

        if account_id is None:
            options = "\n".join(
                f"- {account.name} ({account.type.value}): {account.id}" for account in accounts
            )
            return (
                "Multiple accounts are available. Run /connect again with an account_id:\n"
                f"{options}"
            )

        account = await self.account_repo.get_by_id(account_id)
        if account is None or account.user_id != user.id:
            return "That account_id was not found for this user."

        await self.link_repo.upsert(
            user_id=user.id,
            account_id=account.id,
            chat_id=message.chat.id,
            telegram_user_id=message.from_user.id if message.from_user else None,
            username=message.from_user.username if message.from_user else None,
            first_name=message.from_user.first_name if message.from_user else None,
        )

        return (
            "Telegram is now linked to FinFlow.\n"
            f"Default account: {account.name} ({account.type.value}).\n"
            "Now you can send messages like 'coffee 350 rub' or 'salary 120000'."
        )

    async def _handle_status(self, message: TelegramMessage) -> str:
        link = await self.link_repo.get_by_chat_id(message.chat.id)
        if link is None or not link.is_active:
            return "This chat is not linked yet. Use /connect <api_token> [account_id]."

        await self.link_repo.mark_seen(link)
        account = await self.account_repo.get_by_id(link.account_id)
        if account is None:
            return "This chat is linked, but the configured account is no longer available. Reconnect with /connect."

        return (
            "Telegram input is active.\n"
            f"Account: {account.name} ({account.type.value})\n"
            f"Last seen: {self._format_timestamp(link.last_seen_at)}"
        )

    async def _handle_disconnect(self, message: TelegramMessage) -> str:
        link = await self.link_repo.get_by_chat_id(message.chat.id)
        if link is None or not link.is_active:
            return "This chat is already disconnected."

        await self.link_repo.deactivate(link)
        return "Telegram input has been disconnected for this chat."

    async def _handle_transaction_text(
        self,
        message: TelegramMessage,
        text: str,
    ) -> str:
        link = await self.link_repo.get_by_chat_id(message.chat.id)
        if link is None or not link.is_active:
            return (
                "This chat is not linked to FinFlow yet.\n"
                "Use /connect <api_token> [account_id] first."
            )

        await self.link_repo.mark_seen(link)

        try:
            transaction = await self.parse_create_service.parse_and_create(
                text=text,
                user_id=link.user_id,
                account_id=link.account_id,
            )
        except ValueError as exc:
            return f"Could not create transaction: {exc}"

        return (
            "Saved transaction.\n"
            f"{transaction.type}: {transaction.amount}\n"
            f"{transaction.description}"
        )

    async def _authenticate_api_token(self, raw_token: str) -> User | None:
        tokens = await self.api_token_repo.get_all_active()
        for token in tokens:
            if verify_password(raw_token, token.token_hash):
                await self.api_token_repo.mark_used(token)
                return await self.user_repo.get_by_id(token.user_id)
        return None

    async def _send_message(self, chat_id: int, text: str) -> None:
        if not settings.telegram_bot_token:
            logger.warning("Telegram bot token is not configured; skipping reply")
            return

        url = (
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        )
        payload = {
            "chat_id": chat_id,
            "text": text,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except Exception:
            logger.exception("Failed to send Telegram bot reply")

    def _format_timestamp(self, value: datetime | None) -> str:
        if value is None:
            return "never"
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
