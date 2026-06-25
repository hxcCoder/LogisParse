import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.config import Settings
from app.schemas.extraction import ExtractedLogisticsData
from app.services import document_extractor
from app.services.document_extractor import (
    clean_extracted_text,
    validate_extracted_data,
    extract_text,
    extract_document,
    extract_text_from_pdf,
    extract_text_from_image,
)

# ==========================================
# TESTS PARA: LIMPIEZA DE TEXTO
# ==========================================
def test_clean_extracted_text() -> None:
    raw_text = """
    CONCEPTO
    12345
    Guia: 12345
    12-34-56
    DESTINO DEL VIAJE
    Origen: Santiago
    """
    cleaned = clean_extracted_text(raw_text)
    cleaned_lines = [line.strip() for line in cleaned.split("\n")]
    
    # Lo que debe eliminar (USAR cleaned_lines):
    assert "CONCEPTO" not in cleaned_lines 
    assert "12345" not in cleaned_lines 
    assert "12-34-56" not in cleaned_lines 
    assert "DESTINO DEL VIAJE" not in cleaned_lines 
    
    # Lo que debe mantener (USAR cleaned):
    assert "Guia: 12345" in cleaned
    assert "Origen: Santiago" in cleaned

# ==========================================
# TESTS PARA: VALIDACIÓN SEMÁNTICA
# ==========================================
def test_validate_extracted_data_valid() -> None:
    raw = {
        "origen": "Puerto Montt", 
        "destino": "1234", 
        "chofer": "Juan Perez", 
        "fecha_despacho": "01/01/2026", 
        "numero_guia": "123456", 
        "patente_camion": "ABCD12",  
        "observaciones": "Llegó tarde" 
    }
    
    val = validate_extracted_data(raw)
    
    assert val["origen"] == "Puerto Montt"
    assert val["destino"] is None
    assert val["chofer"] == "Juan Perez"
    assert val["fecha_despacho"] == "01/01/2026"
    assert val["numero_guia"] == "123456"
    assert val["patente_camion"] == "ABCD12"
    assert val["observaciones"] == "Llegó tarde"

def test_validate_extracted_data_invalid_fields() -> None:
    raw = {
        "chofer": "Juan", # Falta apellido
        "fecha_despacho": "2026/01/01", # Formato no soportado
        "numero_guia": "123A", # Tiene letras
        "patente_camion": "A123", # Muy corta
    }
    val = validate_extracted_data(raw)
    
    assert val["chofer"] is None
    assert val["fecha_despacho"] is None
    assert val["numero_guia"] is None
    assert val["patente_camion"] is None

# ==========================================
# TESTS PARA: ENRUTAMIENTO DE EXTRACCIÓN
# ==========================================
def test_extract_text_routes_supported_content_types(monkeypatch) -> None:
    monkeypatch.setattr(document_extractor, "extract_text_from_pdf", lambda *_args: "pdf")
    monkeypatch.setattr(document_extractor, "extract_text_from_image", lambda *_args: "image")

    assert extract_text(b"pdf bytes", "application/pdf") == "pdf"
    assert extract_text(b"image bytes", "image/png") == "image"
    assert extract_text(b"image bytes", "image/jpeg") == "image"
    assert extract_text(b"unsupported", "text/plain") == ""

# ==========================================
# TESTS PARA: ORQUESTADOR ASÍNCRONO
# ==========================================
@pytest.mark.asyncio
async def test_extract_document_rejects_tiny_file() -> None:
    settings = Settings(OPENAI_API_KEY="")
    with pytest.raises(ValueError, match="file too small"):
        await extract_document(b"tiny", "tiny.pdf", "application/pdf", settings)

@pytest.mark.asyncio
async def test_extract_document_returns_empty_when_no_text(monkeypatch) -> None:
    settings = Settings(OPENAI_API_KEY="")
    monkeypatch.setattr(document_extractor, "extract_text", lambda *_args: "")

    result = await extract_document(
        b"123456789012345678901", "blank.pdf", "application/pdf", settings
    )

    assert result.confidence_score == 0.0
    assert result.adapter_used == "None"

@pytest.mark.asyncio
async def test_extract_document_high_confidence_skips_ai(monkeypatch) -> None:
    settings = Settings(OPENAI_API_KEY="sk-test")
    monkeypatch.setattr(document_extractor, "extract_text", lambda *_args: "Valid text")

    # Simulamos un adaptador "perfecto"
    class DummyAdapter:
        async def extract_data(self, *args, **kwargs):
            return {"numero_guia": "123456", "patente_camion": "AB1234", "origen": "Santiago"}
        def calculate_confidence(self, data):
            return 90.0 # Alto puntaje

    monkeypatch.setattr("app.services.document_extractor.AdapterFactory.get_adapter", lambda text: DummyAdapter())

    result = await extract_document(
        b"123456789012345678901", "guide.pdf", "application/pdf", settings
    )

    assert result.numero_guia == "123456"
    assert result.confidence_score == 90.0
    assert result.adapter_used == "DummyAdapter"

@pytest.mark.asyncio
async def test_extract_document_low_confidence_uses_ai_enrichment(monkeypatch) -> None:
    settings = Settings(OPENAI_API_KEY="sk-test")
    monkeypatch.setattr(document_extractor, "extract_text", lambda *_args: "Valid text")

    # Simulamos un adaptador que falla en sacar datos críticos
    class DummyAdapter:
        async def extract_data(self, *args, **kwargs):
            return {"numero_guia": None, "patente_camion": None, "origen": "Santiago"}
        def calculate_confidence(self, data):
            return 40.0 # Bajo puntaje

    monkeypatch.setattr("app.services.document_extractor.AdapterFactory.get_adapter", lambda text: DummyAdapter())

    # Simulamos el GenericLLMAdapter de respaldo que entra a salvar el día
    class DummyGenericLLM:
        async def extract_data(self, *args, **kwargs):
            return {"numero_guia": "999999", "patente_camion": "XX9999", "destino": "Arica"}

    monkeypatch.setattr(document_extractor, "GenericLLMAdapter", DummyGenericLLM)

    result = await extract_document(
        b"123456789012345678901", "guide.pdf", "application/pdf", settings
    )

    # Debe haber fusionado la data
    assert result.origen == "Santiago" # Del adaptador inicial
    assert result.numero_guia == "999999" # Del LLM
    assert result.patente_camion == "XX9999" # Del LLM
    assert result.adapter_used is not None
    assert "GenericLLM" in result.adapter_used