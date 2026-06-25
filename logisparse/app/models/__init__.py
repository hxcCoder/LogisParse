# app/models/__init__.py
from app.models.base import Base
from app.models.document import (  # <-- DataCorrection debe estar aquí
    DataCorrection,
    Document,
    DocumentStatus,
)
from app.models.user import User

__all__ = ["Base", "Document", "DocumentStatus", "DataCorrection", "User"]
