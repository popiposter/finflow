"""Integration tests for auth repositories.

These tests verify that the user and API token repositories work correctly
with the PostgreSQL database.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.api_token_repository import ApiTokenRepository
from app.repositories.user_repository import UserRepository


@pytest.mark.integration
class TestUserRepository:
    """Tests for UserRepository database operations."""

    @pytest.mark.asyncio
    async def test_create_user(self, clean_db, db_session: AsyncSession) -> None:
        """Test creating a new user."""
        repo = UserRepository(db_session)

        user = await repo.create(
            email="test@example.com",
            hashed_password="hashed_password_hash",
        )

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password_hash"
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, clean_db, db_session: AsyncSession) -> None:
        """Test retrieving a user by ID."""
        repo = UserRepository(db_session)

        user = await repo.create(
            email="test@example.com",
            hashed_password="hashed_password",
        )

        retrieved = await repo.get_by_id(user.id)
        assert retrieved is not None
        assert retrieved.id == user.id
        assert retrieved.email == user.email

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, clean_db, db_session: AsyncSession) -> None:
        """Test retrieving a user by email."""
        repo = UserRepository(db_session)

        user = await repo.create(
            email="test@example.com",
            hashed_password="hashed_password",
        )

        retrieved = await repo.get_by_email("test@example.com")
        assert retrieved is not None
        assert retrieved.id == user.id
        assert retrieved.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(
        self, clean_db, db_session: AsyncSession
    ) -> None:
        """Test retrieving a user by email that doesn't exist."""
        repo = UserRepository(db_session)

        retrieved = await repo.get_by_email("nonexistent@example.com")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_update_user(self, clean_db, db_session: AsyncSession) -> None:
        """Test updating a user."""
        repo = UserRepository(db_session)

        user = await repo.create(
            email="test@example.com",
            hashed_password="hashed_password",
        )

        user.is_active = False
        updated = await repo.update(user)

        assert updated.is_active is False


@pytest.mark.integration
class TestApiTokenRepository:
    """Tests for ApiTokenRepository database operations."""

    @pytest.mark.asyncio
    async def test_create_api_token(self, clean_db, db_session: AsyncSession) -> None:
        """Test creating a new API token."""
        from datetime import timedelta

        repo = ApiTokenRepository(db_session)

        # First create a user
        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="test@example.com",
            hashed_password="hashed_password",
        )

        token = await repo.create(
            user_id=user.id,
            name="Test Token",
            token_hash="token_hash_123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        )

        assert token.id is not None
        assert token.user_id == user.id
        assert token.name == "Test Token"
        assert token.token_hash == "token_hash_123"
        assert token.is_revoked is False

    @pytest.mark.asyncio
    async def test_get_token_by_hash(self, clean_db, db_session: AsyncSession) -> None:
        """Test retrieving an API token by its hash."""
        from datetime import timedelta

        repo = ApiTokenRepository(db_session)

        # First create a user and token
        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="test@example.com",
            hashed_password="hashed_password",
        )

        token = await repo.create(
            user_id=user.id,
            name="Test Token",
            token_hash="unique_hash_xyz",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        )

        retrieved = await repo.get_by_hash("unique_hash_xyz")
        assert retrieved is not None
        assert retrieved.id == token.id
        assert retrieved.token_hash == "unique_hash_xyz"

    @pytest.mark.asyncio
    async def test_get_active_by_user(self, clean_db, db_session: AsyncSession) -> None:
        """Test retrieving active tokens for a user."""
        from datetime import timedelta

        repo = ApiTokenRepository(db_session)
        user_repo = UserRepository(db_session)

        user = await user_repo.create(
            email="test@example.com",
            hashed_password="hashed_password",
        )

        # Create multiple tokens
        now = datetime.now(timezone.utc)
        await repo.create(
            user_id=user.id,
            name="Active Token 1",
            token_hash="hash1",
            expires_at=now + timedelta(days=365),
        )
        await repo.create(
            user_id=user.id,
            name="Active Token 2",
            token_hash="hash2",
            expires_at=now + timedelta(days=365),
        )
        await repo.create(
            user_id=user.id,
            name="Revoked Token",
            token_hash="hash3",
            expires_at=now + timedelta(days=365),
        )
        await repo.create(
            user_id=user.id,
            name="Expired Token",
            token_hash="hash4",
            expires_at=now - timedelta(days=1),
        )

        # Mark one as revoked
        revoked = await repo.get_by_hash("hash3")
        await repo.revoke(revoked)

        # Get active tokens
        active_tokens = await repo.get_active_by_user(user.id)

        assert len(active_tokens) == 2
        token_hashes = [t.token_hash for t in active_tokens]
        assert "hash1" in token_hashes
        assert "hash2" in token_hashes
        assert "hash3" not in token_hashes  # Revoked
        assert "hash4" not in token_hashes  # Expired

    @pytest.mark.asyncio
    async def test_revoke_token(self, clean_db, db_session: AsyncSession) -> None:
        """Test revoking an API token."""
        from datetime import timedelta

        repo = ApiTokenRepository(db_session)

        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="test@example.com",
            hashed_password="hashed_password",
        )

        token = await repo.create(
            user_id=user.id,
            name="Test Token",
            token_hash="hash_to_revoke",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        )

        assert token.is_revoked is False

        revoked = await repo.revoke(token)
        assert revoked.is_revoked is True

    @pytest.mark.asyncio
    async def test_mark_token_as_used(self, clean_db, db_session: AsyncSession) -> None:
        """Test marking a token as used."""

        repo = ApiTokenRepository(db_session)

        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="test@example.com",
            hashed_password="hashed_password",
        )

        token = await repo.create(
            user_id=user.id,
            name="Test Token",
            token_hash="hash_used",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        )

        assert token.last_used_at is None

        now = datetime.now(timezone.utc)
        updated = await repo.mark_used(token, now)
        assert updated.last_used_at == now
