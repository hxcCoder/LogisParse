"""Tests for Pydantic schemas validation."""

import pytest
from pydantic import ValidationError

from app.schemas.document import DocumentResponse
from app.schemas.extraction import ExtractedLogisticsData
from app.schemas.token import TokenResponse
from app.schemas.user import UserCreate, UserLogin


def test_user_create_validation() -> None:
    """Test UserCreate schema validation."""
    # Valid user
    user = UserCreate(email="test@example.com", password="validpassword123", full_name="Test")
    assert user.email == "test@example.com"

    # Invalid email
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", password="validpassword123", full_name="Test")


def test_user_login_validation() -> None:
    """Test UserLogin schema validation."""
    login = UserLogin(email="test@example.com", password="password123")
    assert login.email == "test@example.com"

    with pytest.raises(ValidationError):
        UserLogin(email="invalid-email", password="password123")


def test_token_response_validation() -> None:
    """Test TokenResponse schema validation."""
    token = TokenResponse(access_token="abc123", token_type="bearer")
    assert token.token_type == "bearer"


def test_extracted_logistics_data_validation() -> None:
    """Test ExtractedLogisticsData schema."""
    data = ExtractedLogisticsData(
        origen="Puerto Montt",
        destino="Puerto Varas",
        patente_camion="ABC-1234",
        fecha_despacho="2026-05-29",
        items=[
            {"sku": "SALMON-001", "cantidad": 100},
            {"sku": "SALMON-002", "cantidad": 250},
        ],
    )
    assert data.origen == "Puerto Montt"
    assert len(data.items) == 2


def test_document_response_validation() -> None:
    """Test DocumentResponse schema."""
    from datetime import datetime

    doc = DocumentResponse(
        id="doc-123",
        filename="guide.pdf",
        content_type="application/pdf",
        status="PENDING",
        uploaded_at=datetime.now(),
    )
    assert doc.filename == "guide.pdf"
    assert doc.status == "PENDING"
