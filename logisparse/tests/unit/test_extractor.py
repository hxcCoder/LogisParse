import sys

import pytest

from app.core.config import Settings
from app.schemas.extraction import ExtractedLogisticsData
from app.services import document_extractor
from app.services.document_extractor import (
    AI_CONTEXT_CHAR_LIMIT,
    RegexResult,
    ai_complete,
    build_ai_context,
    extract_document,
    extract_text,
    extract_text_from_image,
    extract_text_from_pdf,
    missing_fields,
    run_regex,
    to_schema,
)


def test_run_regex_full_document() -> None:
    text = """
    Origen: Puerto Montt
    Destino: Santiago
    Chofer: Juan Perez
    Patente: AB1234
    Guia: 123456
    10 kg Salmon Atlantico
    5 cajas hielo
    """

    result = run_regex(text)

    assert result.origen == "Puerto Montt"
    assert result.destino == "Santiago"
    assert result.chofer == "Juan Perez"
    assert result.patente == "AB1234"
    assert result.guia == "123456"
    assert len(result.items) >= 1


def test_run_regex_partial_document() -> None:
    result = run_regex("Origen: Puerto Montt")
    missing = missing_fields(result)

    assert "origen" not in missing
    assert "destino" in missing
    assert "chofer" in missing
    assert "patente" in missing
    assert "fecha" in missing
    assert "guia" in missing


def test_to_schema_mapping() -> None:
    text = """
    Origen: A
    Destino: B
    Chofer: C
    Patente: ZZ9999
    Guia: 7777
    2 kg pescado
    """

    schema = to_schema(run_regex(text))

    assert schema.origen == "A"
    assert schema.destino == "B"
    assert schema.patente_camion == "ZZ9999"
    assert schema.numero_guia == "7777"
    assert len(schema.items) >= 1


def test_extract_text_returns_empty_for_unsupported_content_type() -> None:
    assert extract_text(b"plain text", "text/plain") == ""


def test_extract_text_routes_supported_content_types(monkeypatch) -> None:
    monkeypatch.setattr(document_extractor, "extract_text_from_pdf", lambda *_args: "pdf")
    monkeypatch.setattr(document_extractor, "extract_text_from_image", lambda *_args: "image")

    assert extract_text(b"pdf bytes", "application/pdf") == "pdf"
    assert extract_text(b"image bytes", "image/png") == "image"
    assert extract_text(b"image bytes", "image/jpeg") == "image"


def test_pdf_extraction_returns_empty_when_dependency_is_missing(monkeypatch) -> None:
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "pdfplumber":
            raise ImportError("missing pdfplumber")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    assert extract_text_from_pdf(b"%PDF-1.7 fake content") == ""


def test_image_extraction_returns_empty_when_dependency_is_missing(monkeypatch) -> None:
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name in {"pytesseract", "PIL"}:
            raise ImportError("missing OCR dependency")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    assert extract_text_from_image(b"\x89PNG\r\n\x1a\n") == ""


def test_build_ai_context_uses_only_relevant_fragments() -> None:
    text = "\n".join(
        [
            "Linea administrativa sin datos utiles " * 20,
            "Destino: Centro de distribucion Santiago",
            "Otra linea larga que no deberia viajar a IA " * 20,
            "Patente camion: ABCD12",
            "Observacion final irrelevante " * 20,
        ]
    )

    context = build_ai_context(text, ["destino", "patente"])

    assert "Destino: Centro de distribucion Santiago" in context
    assert "Patente camion: ABCD12" in context
    assert "Otra linea larga" not in context
    assert len(context) <= AI_CONTEXT_CHAR_LIMIT


def test_build_ai_context_skips_blank_lines_and_stops_at_limit() -> None:
    text = "\n\n".join([f"Destino: linea relevante {index}" for index in range(80)])

    context = build_ai_context(text, ["destino"])

    assert context.startswith("Destino: linea relevante 0")
    assert len(context) <= AI_CONTEXT_CHAR_LIMIT


def test_build_ai_context_falls_back_to_short_text_when_no_keywords() -> None:
    text = " ".join(["sin etiquetas claras"] * 100)

    context = build_ai_context(text, ["guia"])

    assert context.startswith("sin etiquetas claras")
    assert len(context) <= document_extractor.AI_CONTEXT_FALLBACK_CHARS


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
    Guia: 123456
    01/01/2026
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
async def test_extract_document_skips_ai_when_confidence_is_high_enough(monkeypatch) -> None:
    settings = Settings(OPENAI_API_KEY="sk-test")
    text = """
    Origen: Puerto Montt
    Destino: Santiago
    Chofer: Juan Perez
    AB1234
    01/01/2026
    """
    monkeypatch.setattr(document_extractor, "extract_text", lambda *_args: text)

    async def fail_if_called(*_args):
        raise AssertionError("AI should not be called when regex confidence is enough")

    monkeypatch.setattr(document_extractor, "ai_complete", fail_if_called)

    result = await extract_document(
        b"%PDF-1.7 enough bytes", "guide.pdf", "application/pdf", settings
    )

    assert result.numero_guia is None
    assert result.origen == "Puerto Montt"


@pytest.mark.asyncio
async def test_ai_complete_without_api_key_returns_regex_schema() -> None:
    settings = Settings(OPENAI_API_KEY="")
    regex_result = RegexResult(origen="A", destino="B", confidence=0.2)

    result = await ai_complete("Origen: A", regex_result, ["chofer"], settings)

    assert result.origen == "A"
    assert result.destino == "B"


@pytest.mark.asyncio
async def test_ai_complete_sends_compact_context_and_merges_regex_first(
    monkeypatch,
) -> None:
    captured = {}

    class FakeResponses:
        async def parse(self, **kwargs):
            captured.update(kwargs)

            class Response:
                output_parsed = ExtractedLogisticsData(
                    origen="AI should not replace regex",
                    destino="Santiago",
                    patente_camion="ZZ9999",
                    observaciones="Validado con fragmentos",
                )

            return Response()

    class FakeClient:
        responses = FakeResponses()

    class FakeOpenAI:
        def AsyncOpenAI(self, api_key=None):
            return FakeClient()

    monkeypatch.setitem(sys.modules, "openai", FakeOpenAI())

    settings = Settings(OPENAI_API_KEY="sk-test", OPENAI_MODEL="gpt-test")
    regex_result = RegexResult(origen="Puerto Montt", confidence=0.2)
    noisy_text = "\n".join(
        [
            "bloque de texto irrelevante " * 80,
            "Destino: Santiago",
            "Patente: ZZ9999",
            "otro bloque irrelevante " * 80,
        ]
    )

    result = await ai_complete(noisy_text, regex_result, ["destino", "patente"], settings)

    user_text = captured["input"][1]["content"][0]["text"]
    assert captured["model"] == "gpt-test"
    assert "Destino: Santiago" in user_text
    assert "bloque de texto irrelevante" not in user_text
    assert result.origen == "Puerto Montt"
    assert result.destino == "Santiago"
    assert result.patente_camion == "ZZ9999"
