# app/schemas/extraction.py

from pydantic import BaseModel, ConfigDict, Field


class ExtractedLogisticsData(BaseModel):
    """
    Modelo base para los datos extraídos de documentos logísticos y tributarios chilenos.
    Contiene campos estándar del SII más campos dinámicos.
    """

    # ── Campos de documento tributario chileno (SII) ──
    rut_emisor: str | None = Field(
        default=None,
        description="RUT del emisor de la guía/factura (ej: 76.123.456-K)"
    )
    rut_receptor: str | None = Field(
        default=None,
        description="RUT del receptor (ej: 77.654.321-0)"
    )
    folio_sii: str | None = Field(
        default=None,
        description="Folio electrónico SII o número de guía"
    )
    fecha_emision: str | None = Field(
        default=None,
        description="Fecha de emisión del documento (formato dd/mm/aaaa)"
    )
    monto_total: str | None = Field(
        default=None,
        description="Monto total del documento en pesos chilenos"
    )

    # ── Campos logísticos ──
    origen: str | None = None
    destino: str | None = None
    patente_camion: str | None = None
    chofer: str | None = None
    fecha_despacho: str | None = None
    numero_guia: str | None = None
    observaciones: str | None = None

    # ── Metadatos de auditoría SaaS ──
    adapter_used: str | None = Field(
        default=None,
        description="El adaptador específico que procesó este documento"
    )
    confidence_score: float | None = Field(
        default=None,
        description="Puntaje de precisión (0-100)"
    )

    model_config = ConfigDict(extra="allow")