"""
Integration tests for API endpoints.

Covers auth flow, document upload/list/get, access control, and pagination.
All external processing (OCR / AI) is mocked to ensure deterministic tests.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.schemas.extraction import ExtractedLogisticsData

# ─────────────────────────────────────────────────────────────
# MOCK GLOBAL (extractor)
# ─────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def mock_document_extractor():
    """Avoid OCR + OpenAI calls in integration tests."""
    with patch("app.api.v1.documents.extract_document") as mock:
        mock.return_value = ExtractedLogisticsData(
            origen="Puerto Montt",
            destino="Santiago",
            patente_camion="ABCD12",
            chofer="Juan Perez",
            fecha_despacho="2026-01-01",
            numero_guia="12345",
            observaciones=None,
        )
        yield mock


# ── helpers ──────────────────────────────────────────────────


def _register(client: TestClient, email: str, password: str = "strong-password") -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert response.status_code == 201


def _login(client: TestClient, email: str, password: str = "strong-password") -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _register_and_login(client: TestClient, email: str, password: str = "strong-password") -> str:
    _register(client, email, password)
    return _login(client, email, password)


def _upload_pdf(client: TestClient, token: str, filename: str = "guide.pdf") -> dict:
    response = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, b"%PDF-1.7 fake content", "application/pdf")},
    )
    assert response.status_code == 201
    return response.json()


# ── system endpoints ─────────────────────────────────────────


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "X-Request-ID" in response.headers


def test_root_endpoint(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()


# ── auth ─────────────────────────────────────────────────────


def test_register_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "strong-password",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "newuser@example.com"
    assert body["is_active"] is True
    assert "id" in body
    assert "hashed_password" not in body


def test_register_duplicate_email_returns_400(client: TestClient) -> None:
    payload = {"email": "dup@example.com", "password": "strong-password", "full_name": "User"}
    client.post("/api/v1/auth/register", json=payload)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400


def test_login_returns_bearer_token(client: TestClient) -> None:
    _register(client, "login@example.com")
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "strong-password"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    _register(client, "wrongpass@example.com", "correct-password")
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


# ── documents ───────────────────────────────────────────────


def test_document_list_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/documents")
    assert response.status_code == 403


def test_upload_valid_pdf(client: TestClient) -> None:
        token = _register_and_login(client, "u1@example.com")
        body = _upload_pdf(client, token)
        assert body["filename"] == "guide.pdf"
        assert body["content_type"] == "application/pdf"
        # CAMBIA ESTA LÍNEA:
        assert body["status"] == "NEEDS_REVIEW"

def test_upload_valid_png(client: TestClient) -> None:
    token = _register_and_login(client, "png@example.com")
    response = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("image.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    assert response.status_code == 201
    assert response.json()["content_type"] == "image/png"


def test_upload_valid_jpeg(client: TestClient) -> None:
    token = _register_and_login(client, "jpg@example.com")
    response = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("photo.jpg", b"\xff\xd8\xff\xe0", "image/jpeg")},
    )
    assert response.status_code == 201
    assert response.json()["content_type"] == "image/jpeg"


def test_upload_marks_failed_on_validation_error(
    client: TestClient,
    mock_document_extractor,
) -> None:
    mock_document_extractor.side_effect = ValueError("bad document")
    token = _register_and_login(client, "extract-value-error@example.com")

    response = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("guide.pdf", b"%PDF-1.7 fake content", "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "FAILED"
    assert body["error_logs"] == "bad document"


def test_upload_marks_failed_on_unexpected_extraction_error(
    client: TestClient,
    mock_document_extractor,
) -> None:
    mock_document_extractor.side_effect = RuntimeError("boom")
    token = _register_and_login(client, "extract-runtime-error@example.com")

    response = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("guide.pdf", b"%PDF-1.7 fake content", "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "FAILED"
    assert body["error_logs"] == "Extraction failed unexpectedly"


def test_upload_rejects_extension_content_mismatch(client: TestClient) -> None:
    token = _register_and_login(client, "mismatch@example.com")
    response = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("guide.pdf", b"\x89PNG fake", "application/pdf")},
    )
    assert response.status_code == 400


def test_upload_rejects_unsupported_extension(client: TestClient) -> None:
    token = _register_and_login(client, "unsupported@example.com")
    response = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("document.docx", b"PK\x03\x04", "application/vnd.openxmlformats")},
    )
    assert response.status_code == 400


def test_get_document_list(client: TestClient) -> None:
    token = _register_and_login(client, "list@example.com")
    for i in range(3):
        _upload_pdf(client, token, f"doc{i}.pdf")

    response = client.get(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    docs = response.json()
    assert isinstance(docs, list)
    assert len(docs) == 3


def test_get_specific_document(client: TestClient) -> None:
    token = _register_and_login(client, "specific@example.com")
    doc = _upload_pdf(client, token, "specific.pdf")

    response = client.get(
        f"/api/v1/documents/{doc['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == doc["id"]
    assert response.json()["filename"] == "specific.pdf"


def test_get_nonexistent_document_returns_404(client: TestClient) -> None:
    token = _register_and_login(client, "notfound@example.com")
    response = client.get(
        "/api/v1/documents/nonexistent-uuid",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_access_other_user_document_returns_403(client: TestClient) -> None:
    token1 = _register_and_login(client, "user1@example.com")
    doc = _upload_pdf(client, token1)

    token2 = _register_and_login(client, "user2@example.com")
    response = client.get(
        f"/api/v1/documents/{doc['id']}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 403


def test_pagination_limit(client: TestClient) -> None:
    token = _register_and_login(client, "paginate@example.com")
    for i in range(5):
        _upload_pdf(client, token, f"doc{i}.pdf")

    response = client.get(
        "/api/v1/documents?limit=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_pagination_skip(client: TestClient) -> None:
    token = _register_and_login(client, "skip@example.com")
    for i in range(4):
        _upload_pdf(client, token, f"doc{i}.pdf")

    all_docs = client.get(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    skipped = client.get(
        "/api/v1/documents?skip=2",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    assert len(skipped) < len(all_docs)
