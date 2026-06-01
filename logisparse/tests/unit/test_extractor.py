import pytest

from app.core.config import Settings
from app.schemas.extraction import ExtractedLogisticsData
from app.services import document_extractor
from app.services.document_extractor import (
    RegexResult,
    ai_complete,
    extract_document,
    missing_fields,
    run_regex,
    to_schema,
)


def test_run_regex_full_document():
    text = """
    Origen: Puerto Montt
    Destino: Santiago
    Chofer: Juan Perez
    Patente: AB1234
    Guía: 123456
    10 kg Salmon Atlantico
    5 cajas hielo
    """

    r = run_regex(text)

    assert r.origen == "Puerto Montt"
    assert r.destino == "Santiago"
    assert r.chofer == "Juan Perez"
    assert r.patente == "AB1234"
    assert r.guia == "123456"

    assert r.items is not None
    assert len(r.items) >= 1


def test_run_regex_partial_document():
    text = "Origen: Puerto Montt"

    r = run_regex(text)
    missing = missing_fields(r)

    assert "destino" in missing
    assert "chofer" in missing
    assert "patente" in missing


def test_to_schema_mapping():
    text = """
    Origen: A
    Destino: B
    Chofer: C
    Patente: ZZ9999
    Guía: 7777
    2 kg pescado
    """

    r = run_regex(text)
    schema = to_schema(r)

    assert schema.origen == "A"
    assert schema.destino == "B"
    assert schema.patente_camion == "ZZ9999"
    assert schema.numero_guia == "7777"
    assert len(schema.items) >= 1


@pytest.mark.asyncio
async def test_extract_document_rejects_tiny_file() -> None:
    settings = Settings(OPENAI_API_KEY="")

    with pytest.raises(ValueError, match="file too small"):
        await extract_document(b"tiny", "tiny.pdf", "application/pdf", settings)


@pytest.mark.asyncio
async def test_extract_document_returns_empty_schema_when_text_missing(monkeypatch) -> None:
    settings = Settings(OPENAI_API_KEY="")
    monkeypatch.setattr(document_extractor, "extract_text", lambda *_args: "")

    result = await extract_document(
        b"%PDF-1.7 enough bytes", "blank.pdf", "application/pdf", settings
    )

    assert result == ExtractedLogisticsData()


@pytest.mark.asyncio
async def test_extract_document_uses_regex_when_complete(monkeypatch) -> None:
    settings = Settings(OPENAI_API_KEY="sk-test")
    text = """
    Origen: Puerto Montt
    Destino: Santiago
    Chofer: Juan Perez
    AB1234
    Guía: 123456
    10 kg Salmon
    """
    monkeypatch.setattr(document_extractor, "extract_text", lambda *_args: text)

    result = await extract_document(
        b"%PDF-1.7 enough bytes", "guide.pdf", "application/pdf", settings
    )

    assert result.origen == "Puerto Montt"
    assert result.destino == "Santiago"
    assert result.numero_guia == "123456"


@pytest.mark.asyncio
async def test_extract_document_calls_ai_for_low_confidence(monkeypatch) -> None:
    settings = Settings(OPENAI_API_KEY="sk-test")
    monkeypatch.setattr(document_extractor, "extract_text", lambda *_args: "Origen: Puerto Montt")

    async def fake_ai_complete(*_args):
        return ExtractedLogisticsData(origen="Puerto Montt", destino="Santiago")

    monkeypatch.setattr(document_extractor, "ai_complete", fake_ai_complete)

    result = await extract_document(
        b"%PDF-1.7 enough bytes", "guide.pdf", "application/pdf", settings
    )

    assert result.destino == "Santiago"


@pytest.mark.asyncio
async def test_ai_complete_without_api_key_returns_regex_schema() -> None:
    settings = Settings(OPENAI_API_KEY="")
    regex_result = RegexResult(origen="A", destino="B", confidence=0.2)

    result = await ai_complete("Origen: A", regex_result, ["chofer"], settings)

    assert result.origen == "A"
    assert result.destino == "B"
