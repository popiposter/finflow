"""Unit tests for security helpers."""

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_token,
    hash_api_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_password_creates_different_hashes(self) -> None:
        """Test that hashing the same password multiple times creates different hashes."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert len(hash1) > 0
        assert len(hash2) > 0

    def test_verify_password_returns_true_for_valid_password(self) -> None:
        """Test verification returns True for correct password."""
        password = "test_password_123"
        password_hash = hash_password(password)

        assert verify_password(password, password_hash) is True

    def test_verify_password_returns_false_for_invalid_password(self) -> None:
        """Test verification returns False for incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        password_hash = hash_password(password)

        assert verify_password(wrong_password, password_hash) is False

    def test_verify_password_returns_false_for_empty_password(self) -> None:
        """Test verification returns False for empty password."""
        password = "test_password_123"
        password_hash = hash_password(password)

        assert verify_password("", password_hash) is False


class TestAccessToken:
    """Tests for access token creation and decoding."""

    def test_create_access_token_contains_subject(self) -> None:
        """Test access token contains user ID as subject."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(user_id)
        payload = decode_token(token)

        assert payload["sub"] == user_id

    def test_create_access_token_has_correct_type(self) -> None:
        """Test access token has type 'access'."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(user_id)
        payload = decode_token(token)

        assert payload["type"] == "access"

    def test_create_access_token_has_exp_claim(self) -> None:
        """Test access token has expiration claim."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(user_id)
        payload = decode_token(token)

        assert "exp" in payload

    def test_create_access_token_has_iat_claim(self) -> None:
        """Test access token has issue at claim."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(user_id)
        payload = decode_token(token)

        assert "iat" in payload


class TestRefreshToken:
    """Tests for refresh token creation and decoding."""

    def test_create_refresh_token_contains_subject(self) -> None:
        """Test refresh token contains user ID as subject."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_refresh_token(user_id)
        payload = decode_token(token)

        assert payload["sub"] == user_id

    def test_create_refresh_token_has_correct_type(self) -> None:
        """Test refresh token has type 'refresh'."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_refresh_token(user_id)
        payload = decode_token(token)

        assert payload["type"] == "refresh"

    def test_create_refresh_token_has_longer_expiry(self) -> None:
        """Test refresh token has longer expiry than access token."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        # Refresh token should expire later than access token
        assert refresh_payload["exp"] > access_payload["exp"]


class TestApiToken:
    """Tests for API token generation and hashing."""

    def test_generate_api_token_returns_random_token(self) -> None:
        """Test that generating tokens returns different random tokens."""
        token1 = generate_api_token()
        token2 = generate_api_token()

        assert token1 != token2
        assert len(token1) > 0
        assert len(token2) > 0

    def test_hash_api_token_returns_different_hash(self) -> None:
        """Test that hashing API token creates different hash."""
        token = "test_api_token_xyz123"
        hash1 = hash_api_token(token)
        hash2 = hash_api_token(token)

        assert hash1 != hash2

    def test_hash_api_token_can_be_verified(self) -> None:
        """Test that hashed API token can be verified."""
        token = "test_api_token_xyz123"
        token_hash = hash_api_token(token)

        # Using pwdlib directly to verify
        import pwdlib

        hasher = pwdlib.PasswordHash.recommended()
        assert hasher.verify(token, token_hash) is True


class TestTokenValidation:
    """Tests for token validation."""

    def test_decode_rejects_invalid_token(self) -> None:
        """Test decoding rejects invalid token string."""
        # JWT library raises various exceptions for invalid tokens
        # Using jwt.exceptions.DecodeError as a more specific exception type
        import jwt.exceptions

        with pytest.raises(jwt.exceptions.DecodeError):
            decode_token("invalid.token.string")

    def test_decode_rejects_modified_token(self) -> None:
        """Test decoding rejects modified token."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(user_id)

        # Modify the token
        parts = token.split(".")
        parts[1] = "modified"
        modified_token = ".".join(parts)

        # JWT decoding raises different exception types depending on what's wrong
        import jwt.exceptions

        with pytest.raises(jwt.exceptions.DecodeError):
            decode_token(modified_token)
