# app/schemas/document.py
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.schemas.extraction import ExtractedLogisticsData


class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    FAILED = "FAILED"
    # NUEVO ESTADO: Si el confidence_score es bajo, pausamos para corrección humana
    NEEDS_REVIEW = "NEEDS_REVIEW"


class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str | None = None
    status: DocumentStatus
    extracted_data: ExtractedLogisticsData | None = None
    error_logs: str | None = None
    created_at: datetime
    updated_at: datetime

    # Permite a Pydantic leer directamente desde los modelos SQLAlchemy (ORM)
    model_config = ConfigDict(from_attributes=True)


class DataCorrectionCreate(BaseModel):
    """Esquema para recibir la corrección desde el frontend (Next.js)"""

    field_name: str
    original_value: str | None = None
    corrected_value: str
    adapter_used: str | None = None


class DataCorrectionResponse(BaseModel):
    """Esquema para devolver la corrección guardada como confirmación"""

    id: str
    document_id: str
    field_name: str
    original_value: str | None = None
    corrected_value: str | None = None
    adapter_used: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
