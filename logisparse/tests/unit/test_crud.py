"""Tests for CRUD operations."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_document import (
    create_document,
    get_user_documents,
    update_document_status,
)
from app.crud.crud_user import authenticate_user, create_user, get_user_by_email
from app.models.document import DocumentStatus


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession) -> None:
    """Test user creation."""
    user = await create_user(db_session, "test@example.com", "password123456", "Test User")

    assert user.email == "test@example.com"
    assert user.hashed_password != "password123456"


@pytest.mark.asyncio
async def test_get_user_by_email(db_session: AsyncSession) -> None:
    """Test retrieving user by email."""
    await create_user(db_session, "search@example.com", "password123456", "Search User")
    found_user = await get_user_by_email(db_session, "search@example.com")

    assert found_user is not None
    assert found_user.email == "search@example.com"


@pytest.mark.asyncio
async def test_get_nonexistent_user_returns_none(db_session: AsyncSession) -> None:
    """Test retrieving nonexistent user."""
    found_user = await get_user_by_email(db_session, "nonexistent@example.com")
    assert found_user is None


@pytest.mark.asyncio
async def test_authenticate_user(db_session: AsyncSession) -> None:
    """Test user authentication."""
    await create_user(db_session, "auth@example.com", "correct_password_123", "Auth User")
    authenticated = await authenticate_user(db_session, "auth@example.com", "correct_password_123")

    assert authenticated is not None
    assert authenticated.email == "auth@example.com"


@pytest.mark.asyncio
async def test_authenticate_with_wrong_password_returns_none(db_session: AsyncSession) -> None:
    """Test authentication with wrong password."""
    await create_user(db_session, "wrong@example.com", "correct_password_123", "Wrong User")
    authenticated = await authenticate_user(db_session, "wrong@example.com", "wrong_password_000")

    assert authenticated is None


@pytest.mark.asyncio
async def test_create_document(db_session: AsyncSession) -> None:
    """Test document creation."""
    user = await create_user(db_session, "doc_owner@example.com", "password123456", "Doc Owner")

    doc = await create_document(db_session, user.id, "test.pdf", "application/pdf")

    assert doc.filename == "test.pdf"
    assert doc.status == DocumentStatus.PENDING
    assert doc.user_id == user.id


@pytest.mark.asyncio
async def test_update_document_status(db_session: AsyncSession) -> None:
    """Test updating document status."""
    user = await create_user(db_session, "status@example.com", "password123456", "Status User")
    doc = await create_document(db_session, user.id, "status.pdf", "application/pdf")

    updated = await update_document_status(db_session, doc.id, DocumentStatus.EXTRACTED)

    assert updated is not None
    assert updated.status == DocumentStatus.EXTRACTED


@pytest.mark.asyncio
async def test_get_user_documents(db_session: AsyncSession) -> None:
    """Test retrieving user's documents."""
    user = await create_user(db_session, "list@example.com", "password123456", "List User")

    await create_document(db_session, user.id, "doc1.pdf", "application/pdf")
    await create_document(db_session, user.id, "doc2.pdf", "application/pdf")

    docs = await get_user_documents(db_session, user.id)

    assert len(docs) == 2
    assert all(d.user_id == user.id for d in docs)
