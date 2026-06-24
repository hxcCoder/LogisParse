# tests/unit/test_adapters.py
import pytest
from app.services.extractors.specific.starken_adapter import StarkenAdapter
from app.services.extractors.generic_llm_adapter import GenericLLMAdapter
from app.services.extractors.adapter_factory import AdapterFactory, DocumentClassifier

# ---------------------------------------------------------
# Tests para StarkenAdapter (Asíncronos)
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_starken_adapter_successful_extraction():
    adapter = StarkenAdapter()
    text = "Documento de transporte STARKEN. GUIA N° 987654. Patente del vehículo: RT-ZX-11. Conductor: Juan."
    
    # AHORA USAMOS AWAIT
    result = await adapter.extract_data(text)
    
    assert result["numero_guia"] == "987654"
    assert result["patente_camion"] == "RT-ZX-11"
    assert result["origen"] == "Centro Distribución Starken"
    assert result["adapter_used"] == "StarkenAdapter"
    
    score = adapter.calculate_confidence(result)
    assert score == 100.0

@pytest.mark.asyncio
async def test_starken_adapter_missing_data_lowers_confidence():
    adapter = StarkenAdapter()
    text = "Documento de transporte STARKEN. GUIA N° 987654. Patente ilegible."
    
    result = await adapter.extract_data(text)
    
    assert result["numero_guia"] == "987654"
    assert result["patente_camion"] is None
    
    score = adapter.calculate_confidence(result)
    assert score == 70.0

# ---------------------------------------------------------
# Tests para GenericLLMAdapter
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_generic_llm_adapter_confidence():
    adapter = GenericLLMAdapter()
    text = "Llevando carga de Santiago a Puerto Montt."
    
    # Al no pasarle settings, simula un fallo de API por seguridad
    result = await adapter.extract_data(text)
    
    assert result["adapter_used"] == "GenericLLMAdapter (Fallo API)"

# ---------------------------------------------------------
# Tests para el Orquestador: AdapterFactory (Sincronos)
# ---------------------------------------------------------

def test_adapter_factory_routing():
    starken_text = "Comprobante de carga STARKEN - Destino Concepción"
    unknown_text = "Guía de Despacho Transporte Los Lagos EIRL - Ruta 5 Sur"
    
    adapter1 = AdapterFactory.get_adapter(starken_text)
    adapter2 = AdapterFactory.get_adapter(unknown_text)
    
    assert isinstance(adapter1, StarkenAdapter)
    assert isinstance(adapter2, GenericLLMAdapter)

def test_classifier_identifies_starken():
    assert DocumentClassifier.identify_company("envío por starken hoy") == "starken"
    assert DocumentClassifier.identify_company("TURBUS CARGO LOGISTICS") == "starken"
    assert DocumentClassifier.identify_company("Factura genérica sin marca") == "unknown"