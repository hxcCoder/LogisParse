import logging

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import InvalidCredentialsException, UserInactiveException
from app.core.security import decode_token
from app.crud.crud_user import get_user_by_id
from app.models.user import User

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
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
