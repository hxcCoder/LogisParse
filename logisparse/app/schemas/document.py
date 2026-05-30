from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    content_type: str | None
    status: DocumentStatus
    extracted_data: dict[str, Any] | None
    error_logs: str | None
    created_at: datetime
    updated_at: datetime
