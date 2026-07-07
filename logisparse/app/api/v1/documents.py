"""Documents API router.

Upload → validate → extract → store.
Evolucionado a SaaS: Evalúa confidence_score y redirige a revisión humana si es necesario.
"""
from sqlalchemy import select
from app.models.document import Document

import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_settings_dep
from app.core.config import Settings
from app.core.exceptions import DocumentNotFound
from app.crud.crud_document import (
    create_data_correction,  # <-- NUEVO
    create_document,
    get_document_by_id,
    get_recent_corrections,  # <-- NUEVO
    get_user_documents,
    update_document_status,
)
from app.models.document import DocumentStatus
from app.models.user import User
from app.schemas.document import DataCorrectionCreate, DataCorrectionResponse, DocumentResponse
from app.services.document_extractor import extract_document
from app.services.upload_validation import read_and_validate_upload

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: Annotated[UploadFile, File()],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> DocumentResponse:
    filename, content_type, file_content = await read_and_validate_upload(file)

    document = await create_document(
        db=db,
        user_id=current_user.id,
        filename=filename,
        content_type=content_type,
    )

    processing_document = await update_document_status(
        db=db,
        document_id=document.id,
        status=DocumentStatus.PROCESSING,
    )

    if processing_document is None:
        raise DocumentNotFound()

    document = processing_document

    # --- OBTENER HISTORIAL DE CORRECCIONES PARA CONTEXTO ---
    correction_history = await get_recent_corrections(
        db=db,
        user_id=current_user.id,
        limit=5,
    )

    try:
        # Pasamos el historial al orquestador
        extracted_data = await extract_document(
            file_bytes=file_content,
            filename=filename,
            content_type=content_type,
            settings=settings,
            correction_history=correction_history,  # <-- NUEVO
        )

    except ValueError as exc:
        logger.info(
            "Document validation failed for document_id=%s: %s",
            document.id,
            exc,
        )

        failed_document = await update_document_status(
            db=db,
            document_id=document.id,
            status=DocumentStatus.FAILED,
            error_logs=str(exc),
        )

        if failed_document is None:
            raise DocumentNotFound() from exc

        return DocumentResponse.model_validate(failed_document)

    except Exception as exc:
        logger.exception(
            "Unexpected extraction error for document_id=%s",
            document.id,
        )

        failed_document = await update_document_status(
            db=db,
            document_id=document.id,
            status=DocumentStatus.FAILED,
            error_logs="Extraction failed unexpectedly",
        )

        if failed_document is None:
            raise DocumentNotFound() from exc

        return DocumentResponse.model_validate(failed_document)

    # ==========================================
    # NUEVA LÓGICA DE NEGOCIO SaaS (AUDITORÍA)
    # ==========================================
    score = extracted_data.confidence_score or 0.0

    # Decidimos el estado final basado en la confianza de nuestros adaptadores
    final_status = DocumentStatus.EXTRACTED
    if score < 80.0:
        logger.info("Document %s routed to HUMAN REVIEW (Score: %s)", document.id, score)
        final_status = DocumentStatus.NEEDS_REVIEW

    extracted_document = await update_document_status(
        db=db,
        document_id=document.id,
        status=final_status,
        extracted_data=extracted_data.model_dump(),
        error_logs=None,
    )

    if extracted_document is None:
        raise DocumentNotFound()

    return DocumentResponse.model_validate(extracted_document)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    patente: str | None = None,
    numero_guia: str | None = None,
    # ... más campos
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DocumentResponse]:
    # Construir la consulta dinámicamente
    query = select(Document).where(Document.user_id == current_user.id)
    
    if patente:
        # Filtro JSON: extracted_data->>'patente_camion' = patente
        query = query.where(Document.extracted_data["patente_camion"].astext == patente)
    if numero_guia:
        query = query.where(Document.extracted_data["numero_guia"].astext == numero_guia)
    
    query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    documents = result.scalars().all()
    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    document = await get_document_by_id(db, document_id)

    if document is None:
        raise DocumentNotFound()

    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return DocumentResponse.model_validate(document)


# ─── NUEVO ENDPOINT PARA APRENDIZAJE CONTINUO ──────────────


@router.post(
    "/{document_id}/corrections",
    response_model=DataCorrectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_correction(
    document_id: str,
    correction_in: DataCorrectionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DataCorrectionResponse:
    """
    Endpoint para que el humano corrija un campo mal extraído.
    Esto alimenta el sistema de aprendizaje continuo.
    """
    # Verificar que el documento existe y pertenece al usuario
    document = await get_document_by_id(db, document_id)
    if document is None:
        raise DocumentNotFound()
    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Guardar la corrección
    correction = await create_data_correction(
        db=db,
        document_id=document_id,
        correction_in=correction_in,
    )

    return DataCorrectionResponse.model_validate(correction)
