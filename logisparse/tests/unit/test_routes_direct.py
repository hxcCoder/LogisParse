from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.v1 import auth, documents
from app.core.config import Settings
from app.core.security import create_access_token
from app.crud.crud_user import create_user
from app.models.document import DocumentStatus
from app.schemas.extraction import ExtractedLogisticsData
from app.schemas.user import UserCreate, UserLogin


@pytest.mark.asyncio
async def test_register_and_login_route_functions(
    db_session: AsyncSession,
    test_settings: Settings,
) -> None:
    created = await auth.register(
        UserCreate(
            email="direct@example.com",
            password="strong-password",
            full_name="Direct User",
        ),
        db_session,
    )

    token = await auth.login(
        UserLogin(email=created.email, password="strong-password"),
        db_session,
        test_settings,
    )

    assert created.email == "direct@example.com"
    assert token.token_type == "bearer"
    assert token.access_token


@pytest.mark.asyncio
async def test_register_route_rejects_duplicate_email(db_session: AsyncSession) -> None:
    payload = UserCreate(
        email="duplicate-direct@example.com",
        password="strong-password",
        full_name="Duplicate",
    )

    await auth.register(payload, db_session)

    with pytest.raises(HTTPException) as exc_info:
        await auth.register(payload, db_session)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_login_route_rejects_inactive_user(
    db_session: AsyncSession,
    test_settings: Settings,
) -> None:
    user = await create_user(
        db_session,
        "inactive-direct@example.com",
        "strong-password",
        "Inactive",
    )
    user.is_active = False
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await auth.login(
            UserLogin(email="inactive-direct@example.com", password="strong-password"),
            db_session,
            test_settings,
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_current_user_decodes_token(
    db_session: AsyncSession,
    test_settings: Settings,
) -> None:
    user = await create_user(
        db_session,
        "token-direct@example.com",
        "strong-password",
        "Token User",
    )
    token = create_access_token(
        {"sub": user.id},
        test_settings.SECRET_KEY,
        test_settings.ALGORITHM,
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    current_user = await get_current_user(credentials, db_session, test_settings)

    assert current_user.id == user.id


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_token(
    db_session: AsyncSession,
    test_settings: Settings,
) -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-a-token")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials, db_session, test_settings)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_upload_document_route_success(
    db_session: AsyncSession,
    test_settings: Settings,
    monkeypatch,
) -> None:
    user = await create_user(
        db_session,
        "upload-direct@example.com",
        "strong-password",
        "Uploader",
    )

    async def fake_extract_document(**_kwargs):
        return ExtractedLogisticsData(
            origen="Puerto Montt",
            destino="Santiago",
            numero_guia="12345",
            patente_camion="AB1234",
            confidence_score=95.0,
        )

    monkeypatch.setattr(documents, "extract_document", fake_extract_document)
    upload = UploadFile(filename="guide.pdf", file=BytesIO(b"%PDF-1.7 fake content"))

    response = await documents.upload_document(upload, user, db_session, test_settings)

    assert response.status == DocumentStatus.EXTRACTED
    assert response.extracted_data is not None  # <-- Buena práctica para Pylance
    assert response.extracted_data.origen == "Puerto Montt"  # <-- Usa punto, no corchete
    assert response.extracted_data.patente_camion == "AB1234"  # <-- Usa punto, no corchete


@pytest.mark.asyncio
async def test_upload_document_route_marks_failed_on_value_error(
    db_session: AsyncSession,
    test_settings: Settings,
    monkeypatch,
) -> None:
    user = await create_user(
        db_session,
        "upload-failed-direct@example.com",
        "strong-password",
        "Uploader",
    )

    async def fake_extract_document(**_kwargs):
        raise ValueError("formato incompleto")

    monkeypatch.setattr(documents, "extract_document", fake_extract_document)
    upload = UploadFile(filename="guide.pdf", file=BytesIO(b"%PDF-1.7 fake content"))

    response = await documents.upload_document(upload, user, db_session, test_settings)

    assert response.status == DocumentStatus.FAILED
    assert response.error_logs == "formato incompleto"


@pytest.mark.asyncio
async def test_list_and_get_document_route_functions(
    db_session: AsyncSession,
    test_settings: Settings,
    monkeypatch,
) -> None:
    user = await create_user(
        db_session,
        "list-direct@example.com",
        "strong-password",
        "Lister",
    )

    async def fake_extract_document(**_kwargs):
        return ExtractedLogisticsData(origen="Puerto Montt")

    monkeypatch.setattr(documents, "extract_document", fake_extract_document)
    upload = UploadFile(filename="guide.pdf", file=BytesIO(b"%PDF-1.7 fake content"))
    created = await documents.upload_document(upload, user, db_session, test_settings)

    listed = await documents.list_documents(0, 10, user, db_session)
    fetched = await documents.get_document(created.id, user, db_session)

    assert [doc.id for doc in listed] == [created.id]
    assert fetched.filename == "guide.pdf"


@pytest.mark.asyncio
async def test_get_document_route_rejects_other_owner(
    db_session: AsyncSession,
    test_settings: Settings,
    monkeypatch,
) -> None:
    owner = await create_user(db_session, "owner-direct@example.com", "strong-password", "Owner")
    intruder = await create_user(
        db_session,
        "intruder-direct@example.com",
        "strong-password",
        "Intruder",
    )

    async def fake_extract_document(**_kwargs):
        return ExtractedLogisticsData(origen="Puerto Montt")

    monkeypatch.setattr(documents, "extract_document", fake_extract_document)
    upload = UploadFile(filename="guide.pdf", file=BytesIO(b"%PDF-1.7 fake content"))
    created = await documents.upload_document(upload, owner, db_session, test_settings)

    with pytest.raises(HTTPException) as exc_info:
        await documents.get_document(created.id, intruder, db_session)

    assert exc_info.value.status_code == 403
