import os
import pytest
from collections.abc import AsyncGenerator, Generator

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import sys
from pathlib import Path

# ── FIX IMPORT PATH ─────────────────────────────
sys.path.append(str(Path(__file__).resolve().parents[1]))

# ── ENV TEST CONFIG ─────────────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-123456789")
os.environ.setdefault("OPENAI_API_KEY", "")

from app.core.database import get_db
from app.main import app
from app.models import Base


# ── DB FIXTURE ──────────────────────────────────
@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()


# ── CLIENT FIXTURE ──────────────────────────────
@pytest.fixture
def client(db_session: AsyncSession) -> Generator[TestClient, None, None]:

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()