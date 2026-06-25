"""Tests for Pydantic schemas validation."""

from app.models.document import DocumentStatus
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
    data = ExtractedLogisticsData(
        origen="Puerto Montt",
        destino="Santiago",
        numero_guia="12345",
        patente_camion="AB1234",
        chofer="Juan",
        # ¡Elimina la línea de items=[...] que tenías aquí!
    )
    assert data.origen == "Puerto Montt"
    # ¡Elimina el assert data.items que tenías aquí abajo!

def test_document_response_validation() -> None:
    """Test DocumentResponse schema."""
    from datetime import datetime

    doc = DocumentResponse(
        id="doc-123",
        filename="guide.pdf",
        content_type="application/pdf",
        status=DocumentStatus.PENDING,# type: ignore
        created_at=datetime.now(),
        updated_at=datetime.now(),
        extracted_data=None,
        error_logs=None
    )
    assert doc.id == "doc-123"
    assert doc.filename == "guide.pdf"
    assert doc.status == "PENDING"
