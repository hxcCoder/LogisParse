from pydantic import BaseModel, Field


class LogisticsItem(BaseModel):
    sku: str | None = Field(default=None, description="Internal or supplier SKU when present")
    descripcion: str = Field(description="Product or cargo description")
    cantidad: int = Field(ge=0, description="Quantity detected in the document")
    unidad: str | None = Field(default=None, description="Unit of measure")


class ExtractedLogisticsData(BaseModel):
    """Structured payload produced by the AI extraction pipeline."""

    origen: str | None = Field(default=None, description="Dispatch origin")
    destino: str | None = Field(default=None, description="Dispatch destination")
    patente_camion: str | None = Field(default=None, description="Truck plate")
    chofer: str | None = Field(default=None, description="Driver name")
    fecha_despacho: str | None = Field(default=None, description="Dispatch date in YYYY-MM-DD format")
    numero_guia: str | None = Field(default=None, description="Dispatch guide number")
    items: list[LogisticsItem] = Field(default_factory=list, description="Cargo line items")
    observaciones: str | None = Field(default=None, description="Additional observations")
