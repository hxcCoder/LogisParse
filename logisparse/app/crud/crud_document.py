from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document, DocumentStatus, DataCorrection
from app.schemas.document import DataCorrectionCreate

# ── FUNCIONES ORIGINALES DE DOCUMENTOS ───────────────────

async def get_document_by_id(db: AsyncSession, document_id: str) -> Document | None:
    result = await db.execute(select(Document).where(Document.id == document_id))
    return result.scalars().first()

async def get_user_documents(
    db: AsyncSession,
    user_id: str,
    skip: int = 0,
    limit: int = 100,
) -> list[Document]:
    result = await db.execute(
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())

async def create_document(
    db: AsyncSession,
    user_id: str,
    filename: str,
    content_type: str | None,
) -> Document:
    document = Document(
        filename=filename,
        content_type=content_type,
        user_id=user_id,
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document

async def update_document_status(
    db: AsyncSession,
    document_id: str,
    status: DocumentStatus,
    extracted_data: dict[str, Any] | None = None,
    error_logs: str | None = None,
) -> Document | None:
    document = await get_document_by_id(db, document_id)
    if document is None:
        return None
    document.status = status
    if extracted_data is not None:
        document.extracted_data = extracted_data
    if error_logs is not None:
        document.error_logs = error_logs
    await db.commit()
    await db.refresh(document)
    return document


# ── NUEVA FUNCIÓN PARA APRENDIZAJE CONTINUO ──────────────

async def create_data_correction(
    db: AsyncSession,
    document_id: str,
    correction_in: DataCorrectionCreate,
) -> DataCorrection:
    correction = DataCorrection(
        document_id=document_id,
        field_name=correction_in.field_name,
        original_value=correction_in.original_value,
        corrected_value=correction_in.corrected_value,
        adapter_used=correction_in.adapter_used,
    )
    db.add(correction)
    await db.commit()
    await db.refresh(correction)
    return correction