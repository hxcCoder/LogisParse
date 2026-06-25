from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class DocumentStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"  # <-- NUEVO ESTADO PARA EL FLUJO DE AUDITORÍA SAAS


class Document(BaseModel):
    __tablename__ = "documents"
    __table_args__ = (
        Index("idx_documents_user_id", "user_id"),
        Index("idx_documents_status", "status"),
    )

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False, length=30),  # length añadido por seguridad
        default=DocumentStatus.PENDING,
        nullable=False,
    )
    # Aquí se guardan los datos dinámicos extraídos por los Adaptadores (JSONB en Postgres)
    extracted_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_logs: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    user: Mapped[User] = relationship(back_populates="documents")

    # NUEVA RELACIÓN: Un documento puede tener múltiples correcciones hechas por humanos
    corrections: Mapped[list[DataCorrection]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.filename} status={self.status}>"


# ==========================================
# NUEVA TABLA: APRENDIZAJE Y RETROALIMENTACIÓN
# ==========================================
class DataCorrection(BaseModel):
    """
    Registra las correcciones manuales hechas por los usuarios.
    Permite calcular precisión (accuracy) y re-entrenar modelos o mejorar Regex en el futuro.
    """

    __tablename__ = "data_corrections"
    __table_args__ = (Index("idx_corrections_document_id", "document_id"),)

    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), nullable=False)

    # Ej: "patente_camion", "numero_guia"
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Lo que la IA o el Regex creyó que era correcto
    original_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lo que el usuario humano ingresó como verdad absoluta
    corrected_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Para saber a qué adaptador echarle la culpa y mejorar sus reglas
    adapter_used: Mapped[str | None] = mapped_column(String(100), nullable=True)

    document: Mapped[Document] = relationship(back_populates="corrections")

    def __repr__(self) -> str:
        return f"<DataCorrection doc={self.document_id} field={self.field_name}>"
