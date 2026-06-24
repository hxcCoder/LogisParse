# app/schemas/extraction.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class ExtractedLogisticsData(BaseModel):
    """
    Modelo base para los datos extraídos. 
    Contiene los campos estándar, pero permite campos adicionales dinámicamente.
    """
    # Campos base esperados por tu frontend actual (Next.js)
    origen: Optional[str] = None
    destino: Optional[str] = None
    patente_camion: Optional[str] = None
    chofer: Optional[str] = None
    fecha_despacho: Optional[str] = None
    numero_guia: Optional[str] = None
    observaciones: Optional[str] = None

    # Nuevos campos de Auditoría SaaS
    adapter_used: Optional[str] = Field(
        default=None, 
        description="El adaptador específico o de IA que procesó este documento"
    )
    confidence_score: Optional[float] = Field(
        default=None, 
        description="Puntaje de precisión (0-100) para determinar si requiere revisión manual"
    )

    # MAGIA DE ARQUITECTO: Esto permite que si el StarkenAdapter extrae un campo 
    # llamado "peso_carga", Pydantic no lance un error y lo incluya en el JSON de respuesta.
    model_config = ConfigDict(extra='allow')