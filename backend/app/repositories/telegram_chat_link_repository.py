"""Repository for Telegram chat link persistence."""

from datetime import datetime, timezone
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telegram_chat_link import TelegramChatLink


class TelegramChatLinkRepository:
    """Database access for Telegram chat links."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_chat_id(self, chat_id: int) -> TelegramChatLink | None:
        """Return the active link for a Telegram chat if one exists."""
        stmt = select(TelegramChatLink).where(TelegramChatLink.chat_id == chat_id)
        link: TelegramChatLink | None = await self.session.scalar(stmt)
        return link

    async def upsert(
        self,
        *,
        user_id: UUID,
        account_id: UUID,
        chat_id: int,
        telegram_user_id: int | None,
        username: str | None,
        first_name: str | None,
    ) -> TelegramChatLink:
        """Create or update a chat link."""
        link = await self.get_by_chat_id(chat_id)
        now = datetime.now(timezone.utc)

        if link is None:
            link = TelegramChatLink(
                user_id=user_id,
                account_id=account_id,
                chat_id=chat_id,
                telegram_user_id=telegram_user_id,
                username=username,
                first_name=first_name,
                is_active=True,
                last_seen_at=now,
            )
            self.session.add(link)
        else:
            link.user_id = user_id
            link.account_id = account_id
            link.telegram_user_id = telegram_user_id
            link.username = username
            link.first_name = first_name
            link.is_active = True
            link.last_seen_at = now

        await self.session.flush()
        await self.session.refresh(link)
        return link

    async def mark_seen(self, link: TelegramChatLink) -> TelegramChatLink:
        """Update the last-seen timestamp for a linked chat."""
        link.last_seen_at = datetime.now(timezone.utc)
        await self.session.flush()
        return link

    async def deactivate(self, link: TelegramChatLink) -> TelegramChatLink:
        """Deactivate an existing chat link."""
        link.is_active = False
        link.last_seen_at = datetime.now(timezone.utc)
        await self.session.flush()
        return link

    async def list_by_user(self, user_id: UUID) -> list[TelegramChatLink]:
        """List Telegram chat links for a user, newest first."""
        stmt = (
            select(TelegramChatLink)
            .where(TelegramChatLink.user_id == user_id)
            .order_by(TelegramChatLink.created_at.desc())
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_by_id_for_user(self, link_id: UUID, user_id: UUID) -> TelegramChatLink | None:
        """Return a chat link by id if it belongs to the user."""
        stmt = select(TelegramChatLink).where(
            TelegramChatLink.id == link_id,
            TelegramChatLink.user_id == user_id,
        )
        return cast(TelegramChatLink | None, await self.session.scalar(stmt))
