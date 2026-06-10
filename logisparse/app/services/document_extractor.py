"""Hybrid extractor for Chilean logistics and tax documents.

The pipeline is intentionally small:
1. Extract text locally from PDF or image files.
2. Parse deterministic fields with regex.
3. Send only relevant fragments to AI when local parsing is incomplete.
"""

import logging
import re
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any

from app.core.config import Settings
from app.schemas.extraction import ExtractedLogisticsData, LogisticsItem

logger = logging.getLogger(__name__)

AI_THRESHOLD = 0.7
AI_CONTEXT_CHAR_LIMIT = 1200
AI_CONTEXT_FALLBACK_CHARS = 500

FIELD_KEYWORDS = {
    "origen": ("origen", "emisor", "sucursal", "desde"),
    "destino": ("destino", "receptor", "entrega", "hasta"),
    "patente": ("patente", "placa", "camion", "vehiculo"),
    "chofer": ("chofer", "conductor", "transportista"),
    "fecha": ("fecha", "emision", "despacho", "traslado"),
    "guia": ("guia", "folio", "nro", "numero", "dte"),
}

_RE_PATENTE = re.compile(r"\b([A-Z]{2,4}\d{2,4})\b", re.IGNORECASE)
_SPANISH_WORD = r"A-Za-z\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1"
_RE_GUIA = re.compile(r"(?:gu[i\u00ed]a|folio|nro)\s*[:#]?\s*(\d{4,10})", re.I)
_RE_FECHA = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b")
_RE_ORIGEN = re.compile(rf"origen\s*:\s*([{_SPANISH_WORD}]+(?:[ ]+[{_SPANISH_WORD}]+)*)", re.I)
_RE_DESTINO = re.compile(
    rf"destino\s*:\s*([{_SPANISH_WORD}]+(?:[ ]+[{_SPANISH_WORD}]+)*)",
    re.I,
)
_RE_CHOFER = re.compile(
    rf"(?:chofer|conductor)\s*:\s*([{_SPANISH_WORD}]+(?:[ ]+[{_SPANISH_WORD}]+)*)",
    re.I,
)
_RE_ITEM = re.compile(
    rf"(\d+(?:[.,]\d+)?)\s*(kg|caja|cajas|un|unid|lts?)?\s+([{_SPANISH_WORD}\s]{{3,50}})",
    re.I,
)


@dataclass
class RegexResult:
    origen: str | None = None
    destino: str | None = None
    patente: str | None = None
    chofer: str | None = None
    fecha: str | None = None
    guia: str | None = None
    items: list[LogisticsItem] = field(default_factory=list)
    confidence: float = 0.0


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        logger.warning("pdfplumber not installed")
        return ""

    try:
        text = []
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        return "\n".join(text)
    except Exception:
        logger.exception("PDF extraction failed")
        return ""


def extract_text_from_image(file_bytes: bytes) -> str:
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except ImportError:
        logger.warning("OCR dependencies missing")
        return ""

    try:
        img = Image.open(BytesIO(file_bytes))
        return pytesseract.image_to_string(img, lang="spa+eng")
    except Exception:
        logger.exception("Image OCR failed")
        return ""


def extract_text(file_bytes: bytes, content_type: str) -> str:
    if content_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    if content_type in ("image/png", "image/jpeg"):
        return extract_text_from_image(file_bytes)
    return ""


def run_regex(text: str) -> RegexResult:
    result = RegexResult()
    filled = 0
    total = 6

    if match := _RE_ORIGEN.search(text):
        result.origen = match.group(1).strip()
        filled += 1

    if match := _RE_DESTINO.search(text):
        result.destino = match.group(1).strip()
        filled += 1

    if match := _RE_PATENTE.search(text):
        result.patente = match.group(1).upper()
        filled += 1

    if match := _RE_CHOFER.search(text):
        result.chofer = match.group(1).strip()
        filled += 1

    if match := _RE_FECHA.search(text):
        result.fecha = f"{match.group(3)}-{match.group(2):0>2}-{match.group(1):0>2}"
        filled += 1

    if match := _RE_GUIA.search(text):
        result.guia = match.group(1)
        filled += 1

    for match in _RE_ITEM.finditer(text):
        try:
            result.items.append(
                LogisticsItem(
                    cantidad=int(float(match.group(1).replace(",", "."))),
                    unidad=match.group(2),
                    descripcion=match.group(3).strip(),
                )
            )
        except Exception:
            continue

    result.confidence = filled / total
    return result


def missing_fields(result: RegexResult) -> list[str]:
    fields = []
    if not result.origen:
        fields.append("origen")
    if not result.destino:
        fields.append("destino")
    if not result.patente:
        fields.append("patente")
    if not result.chofer:
        fields.append("chofer")
    if not result.fecha:
        fields.append("fecha")
    if not result.guia:
        fields.append("guia")
    return fields


def to_schema(result: RegexResult) -> ExtractedLogisticsData:
    return ExtractedLogisticsData(
        origen=result.origen,
        destino=result.destino,
        patente_camion=result.patente,
        chofer=result.chofer,
        fecha_despacho=result.fecha,
        numero_guia=result.guia,
        items=result.items,
        observaciones=None,
    )


def build_ai_context(text: str, missing: list[str]) -> str:
    """Return a compact text slice with lines likely to contain missing fields."""
    normalized_missing = [field for field in missing if field in FIELD_KEYWORDS]
    keywords = {keyword for field in normalized_missing for keyword in FIELD_KEYWORDS[field]}

    selected: list[str] = []
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        if not line:
            continue

        line_lower = line.lower()
        if any(keyword in line_lower for keyword in keywords):
            selected.append(line)

        if len("\n".join(selected)) >= AI_CONTEXT_CHAR_LIMIT:
            break

    if not selected:
        return " ".join(text.split())[:AI_CONTEXT_FALLBACK_CHARS]

    return "\n".join(selected)[:AI_CONTEXT_CHAR_LIMIT]


async def ai_complete(
    text: str,
    result: RegexResult,
    missing: list[str],
    settings: Settings,
) -> ExtractedLogisticsData:
    """Complete missing fields with OpenAI Structured Outputs."""
    from openai import AsyncOpenAI

    if not settings.OPENAI_API_KEY:
        return to_schema(result)

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    ai_context = build_ai_context(text, missing)

    input_messages: list[Any] = [
        {
            "role": "system",
            "content": (
                "You verify Chilean logistics/tax document fragments. "
                "Return only factual data present in the provided fragments."
            ),
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        f"Missing fields: {', '.join(missing)}\n"
                        f"Known regex data: {to_schema(result).model_dump_json()}\n"
                        f"Relevant fragments:\n{ai_context}"
                    ),
                }
            ],
        },
    ]

    response = await client.responses.parse(
        model=settings.OPENAI_MODEL,
        input=input_messages,
        text_format=ExtractedLogisticsData,
        temperature=0,
    )

    ai = response.output_parsed or ExtractedLogisticsData()

    return ExtractedLogisticsData(
        origen=result.origen or ai.origen,
        destino=result.destino or ai.destino,
        patente_camion=result.patente or ai.patente_camion,
        chofer=result.chofer or ai.chofer,
        fecha_despacho=result.fecha or ai.fecha_despacho,
        numero_guia=result.guia or ai.numero_guia,
        items=result.items if result.items else ai.items,
        observaciones=ai.observaciones,
    )


async def extract_document(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    settings: Settings,
) -> ExtractedLogisticsData:
    if len(file_bytes) < 20:
        raise ValueError("file too small")

    text = extract_text(file_bytes, content_type)
    if not text:
        logger.info("No text extracted from %s", filename)
        return ExtractedLogisticsData()

    regex_result = run_regex(text)
    missing = missing_fields(regex_result)

    if not missing:
        return to_schema(regex_result)

    if regex_result.confidence >= AI_THRESHOLD:
        return to_schema(regex_result)

    return await ai_complete(text, regex_result, missing, settings)
