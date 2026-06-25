# app/schemas/extraction.py

from pydantic import BaseModel, ConfigDict, Field


class ExtractedLogisticsData(BaseModel):
    """
    Modelo base para los datos extraídos.
    Contiene los campos estándar, pero permite campos adicionales dinámicamente.
    """

    # Campos base esperados por tu frontend actual (Next.js)
    origen: str | None = None
    destino: str | None = None
    patente_camion: str | None = None
    chofer: str | None = None
    fecha_despacho: str | None = None
    numero_guia: str | None = None
    observaciones: str | None = None

    # Nuevos campos de Auditoría SaaS
    adapter_used: str | None = Field(
        default=None, description="El adaptador específico o de IA que procesó este documento"
    )
    confidence_score: float | None = Field(
        default=None,
        description="Puntaje de precisión (0-100) para determinar si requiere revisión manual",
    )

    # MAGIA DE ARQUITECTO: Esto permite que si el StarkenAdapter extrae un campo
    # llamado "peso_carga", Pydantic no lance un error y lo incluya en el JSON de respuesta.
    model_config = ConfigDict(extra="allow")
