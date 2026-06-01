"""FastAPI dependency injections.

All dependencies are defined here and explicitly passed to endpoints via Depends().
This ensures:
- No global state in imports
- Full testability via dependency_overrides
- Explicit dependency graph
- Type safety
"""

import logging
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.exceptions import InvalidCredentialsException, UserInactiveException
from app.core.security import decode_token
from app.crud.crud_user import get_user_by_id
from app.models.user import User

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=True)


# ── SETTINGS DEPENDENCY ──────────────────────────────────
def get_settings_dep() -> Settings:
    """Inject Settings instance.

    This can be overridden in tests:
    app.dependency_overrides[get_settings_dep] = lambda: fake_settings
    """
    return get_settings()


# ── DATABASE DEPENDENCY ──────────────────────────────────
async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Inject AsyncSession from FastAPI app.state.session_maker.

    The session_maker must be set during app startup (in lifespan).

    This dependency:
    - Retrieves session_maker from app.state (set during startup)
    - Creates a new session per request
    - Automatically yields and closes the session
    - Can be overridden in tests via app.dependency_overrides[get_db]

    Args:
        request: FastAPI Request object (contains app.state)

    Yields:
        AsyncSession instance for database operations
    """
    session_maker: async_sessionmaker[AsyncSession] = request.app.state.session_maker

    async with session_maker() as session:
        yield session


# ── AUTHENTICATION DEPENDENCY ────────────────────────────
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> User:
    """Inject current authenticated user from JWT token.

    Args:
        credentials: JWT token from Authorization header
        db: Database session
        settings: Settings for JWT decoding

    Returns:
        Authenticated and active User instance

    Raises:
        InvalidCredentialsException: If token is invalid or user not found
        UserInactiveException: If user is not active
    """
    payload = decode_token(credentials.credentials, settings.SECRET_KEY, settings.ALGORITHM)
    if payload is None:
        raise InvalidCredentialsException()

    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise InvalidCredentialsException()

    user = await get_user_by_id(db, user_id)
    if user is None:
        logger.info("Token references missing user_id=%s", user_id)
        raise InvalidCredentialsException()

    if not user.is_active:
        raise UserInactiveException()

    return user
