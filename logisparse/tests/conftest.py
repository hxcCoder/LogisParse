"""Test configuration and fixtures for pytest.

This conftest.py demonstrates:
1. Override get_settings_dep with fake test settings
2. Override get_db with in-memory SQLite session
3. Ensure complete isolation between tests
4. Avoid touching real PostgreSQL or production resources
"""

import asyncio
import os
import sys
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Ensure app is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.deps import get_db, get_settings_dep
from app.core.config import Settings
from app.main import app
from app.models.base import Base


# ── PYTEST CONFIGURATION ──────────────────────────────
def pytest_configure(config):
    """Configure pytest environment before tests run."""
    # Ensure we're NOT using production database
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["SECRET_KEY"] = "test-secret-key-at-least-32-chars-long-!!"
    os.environ["OPENAI_API_KEY"] = "test-key-not-real"
    
    # Register custom markers
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# ── TEST SETTINGS FIXTURE ─────────────────────────────
@pytest.fixture
def test_settings() -> Settings:
    """Provide test Settings with safe defaults."""
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SQLALCHEMY_ECHO=False,
        SECRET_KEY="test-secret-key-at-least-32-chars-long-!!",
        ALGORITHM="HS256",
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
        OPENAI_API_KEY="sk-test",
        APP_TITLE="LogisParse Test",
        APP_VERSION="0.1.0-test",
        DEBUG=True,
        ENVIRONMENT="test",
        ALLOWED_ORIGINS=["http://localhost:3000"],
        MAX_FILE_SIZE_MB=20,
        LOG_LEVEL="DEBUG",
    )


# ── IN-MEMORY DATABASE ───────────────────────────────
@pytest.fixture
async def db_engine():
    """Create in-memory SQLite engine for tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


# ── DATABASE SESSION FIXTURE ──────────────────────────
@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide AsyncSession for tests."""
    session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        yield session


# ── OVERRIDE GET_DB ──────────────────────────────────
@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """Override get_db dependency with test session."""
    async def _get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()


# ── OVERRIDE GET_SETTINGS ────────────────────────────
@pytest.fixture
def override_get_settings(test_settings: Settings):
    """Override get_settings_dep dependency with test settings."""
    def _get_settings() -> Settings:
        return test_settings

    app.dependency_overrides[get_settings_dep] = _get_settings
    yield
    app.dependency_overrides.clear()


# ── TEST CLIENT FIXTURE ───────────────────────────────
@pytest.fixture
def client(
    override_get_db,
    override_get_settings,
) -> Generator[TestClient, None, None]:
    """Provide FastAPI test client with dependencies overridden."""
    with TestClient(app) as test_client:
        yield test_client