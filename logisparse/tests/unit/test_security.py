"""Tests for security utilities."""

from datetime import timedelta

from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_password_hash_roundtrip() -> None:
    """Test password hashing and verification."""
    hashed = hash_password("strong-password-123")

    assert hashed != "strong-password-123"
    assert verify_password("strong-password-123", hashed)
    assert not verify_password("wrong-password", hashed)


def test_jwt_roundtrip() -> None:
    """Test JWT token creation and decoding."""
    secret_key = "test-secret-key-at-least-32-chars-long-!!"
    algorithm = "HS256"

    token = create_access_token(
        {"sub": "user-123"},
        secret_key=secret_key,
        algorithm=algorithm,
        expires_delta=timedelta(minutes=5),
    )
    payload = decode_token(token, secret_key, algorithm)

    assert payload is not None
    assert payload["sub"] == "user-123"
