"""Password hashing and JWT token management.

Functions are designed to be pure or minimal-dependency:
- hash_password/verify_password: Pure password operations (using Argon2)
- create/decode_token: Require settings injection (used via deps.py)
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext


# Use Argon2 instead of bcrypt to avoid passlib/bcrypt compatibility issues
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password using argon2. Pure function, no dependencies."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash. Pure function, no dependencies."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    secret_key: str,
    algorithm: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create JWT access token.

    Args:
        data: Payload data to encode
        secret_key: Secret key for signing
        algorithm: JWT algorithm (e.g., "HS256")
        expires_delta: Optional expiration delta

    Returns:
        JWT token string
    """
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=30))
    payload = data.copy()
    payload.update({"exp": expire})
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_token(token: str, secret_key: str, algorithm: str) -> dict[str, Any] | None:
    """Decode and verify JWT token.

    Args:
        token: JWT token string
        secret_key: Secret key for verification
        algorithm: JWT algorithm (e.g., "HS256")

    Returns:
        Decoded payload dict, or None if invalid
    """
    try:
        return jwt.decode(token, secret_key, algorithms=[algorithm])
    except JWTError:
        return None
