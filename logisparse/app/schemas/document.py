# app/schemas/document.py
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum
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
    content_type: Optional[str] = None
    status: DocumentStatus
    extracted_data: Optional[ExtractedLogisticsData] = None
    error_logs: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Permite a Pydantic leer directamente desde los modelos SQLAlchemy (ORM)
    model_config = ConfigDict(from_attributes=True)
    
class DataCorrectionCreate(BaseModel):
    """Esquema para recibir la corrección desde el frontend (Next.js)"""
    field_name: str
    original_value: Optional[str] = None
    corrected_value: str
    adapter_used: Optional[str] = None

class DataCorrectionResponse(BaseModel):
    """Esquema para devolver la corrección guardada como confirmación"""
    id: str
    document_id: str
    field_name: str
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None
    adapter_used: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)