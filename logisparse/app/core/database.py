"""Database engine and session factory.

Pure functional approach - no global state mutations.
All database resources are created explicitly and managed via FastAPI lifespan.
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import Settings


def build_engine(settings: Settings) -> AsyncEngine:
    """Create AsyncEngine instance based on settings.

    This is a pure function - no side effects, no global state.
    Call this once during app startup and store result in app.state.

    Args:
        settings: Settings instance with database configuration

    Returns:
        Configured AsyncEngine instance
    """
    kwargs: dict[str, object] = {
        "echo": settings.SQLALCHEMY_ECHO,
        "future": True,
        "pool_pre_ping": True,
    }

    # Para PostgreSQL, deshabilitamos la caché de prepared statements
    # para evitar conflictos con PgBouncer en modo transaction/statement.
    if settings.DATABASE_URL.startswith("postgresql"):
        kwargs["connect_args"] = {"statement_cache_size": 0}

    if settings.DATABASE_URL.startswith("sqlite"):
        kwargs["poolclass"] = NullPool
    else:
        kwargs["pool_size"] = settings.DB_POOL_SIZE
        kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

    return create_async_engine(settings.DATABASE_URL, **kwargs)


def build_session_maker(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create AsyncSessionMaker instance.

    This is a pure function - creates a new session factory for the given engine.

    Args:
        engine: AsyncEngine instance

    Returns:
        Configured async_sessionmaker instance
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
