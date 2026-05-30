from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None


def get_config():
    return get_settings()


def build_engine() -> AsyncEngine:
    settings = get_config()

    kwargs: dict[str, object] = {
        "echo": settings.SQLALCHEMY_ECHO,
        "future": True,
        "pool_pre_ping": True,
    }

    if settings.DATABASE_URL.startswith("sqlite"):
        kwargs["poolclass"] = NullPool
    else:
        kwargs["pool_size"] = settings.DB_POOL_SIZE
        kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

    return create_async_engine(settings.DATABASE_URL, **kwargs)


async def init_db() -> None:
    global engine, SessionLocal

    if engine is not None and SessionLocal is not None:
        return

    engine = build_engine()
    SessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def close_db() -> None:
    global engine, SessionLocal

    if engine is not None:
        await engine.dispose()
    engine = None
    SessionLocal = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if SessionLocal is None:
        await init_db()

    if SessionLocal is None:
        raise RuntimeError("Database session factory is not initialized")

    async with SessionLocal() as session:
        yield session