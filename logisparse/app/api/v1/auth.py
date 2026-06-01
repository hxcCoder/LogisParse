from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_settings_dep, get_db
from app.core.config import Settings
from app.core.exceptions import (
    EmailAlreadyRegistered,
    InvalidCredentialsException,
    UserInactiveException,
)
from app.core.security import create_access_token
from app.crud.crud_user import (
    authenticate_user,
    create_user,
    get_user_by_email,
)
from app.schemas.token import TokenResponse
from app.schemas.user import UserCreate, UserLogin, UserResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    existing_user = await get_user_by_email(db, user_data.email)

    if existing_user is not None:
        raise EmailAlreadyRegistered()

    user = await create_user(
        db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
    )

    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> TokenResponse:
    user = await authenticate_user(
        db,
        credentials.email,
        credentials.password,
    )

    if user is None:
        raise InvalidCredentialsException()

    if not user.is_active:
        raise UserInactiveException()

    access_token = create_access_token(
        data={"sub": str(user.id)},
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    )

    return TokenResponse(access_token=access_token)