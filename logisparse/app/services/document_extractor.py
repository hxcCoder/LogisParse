"""
Hybrid document extractor for logistics documents.

Pipeline:
1. Text extraction (PDF OCR / image OCR)
2. Regex extraction (fast deterministic layer)
3. AI fallback (only missing fields)
"""

import base64
import logging
import re
from dataclasses import dataclass, field
from io import BytesIO

from app.schemas.extraction import ExtractedLogisticsData, LogisticsItem

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# TEXT EXTRACTION
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# REGEX
# ─────────────────────────────────────────────────────────────

_RE_PATENTE = re.compile(r"\b([A-Z]{2,4}\d{2,4})\b", re.IGNORECASE)
_RE_RUT = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]\b")
_RE_GUIA = re.compile(r"(?:gu[ií]a|folio|nro)\s*[:#]?\s*(\d{4,10})", re.I)
_RE_FECHA = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b")
_RE_ORIGEN = re.compile(r"origen\s*:\s*([A-Za-záéíóúñ]+(?:[ ]+[A-Za-záéíóúñ]+)*)", re.I)
_RE_DESTINO = re.compile(r"destino\s*:\s*([A-Za-záéíóúñ]+(?:[ ]+[A-Za-záéíóúñ]+)*)", re.I)
_RE_CHOFER = re.compile(r"(?:chofer|conductor)\s*:\s*([A-Za-záéíóúñ]+(?:[ ]+[A-Za-záéíóúñ]+)*)", re.I)

_RE_ITEM = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(kg|caja|cajas|un|unid|lts?)?\s+([A-Za-záéíóúñ\s]{3,50})",
    re.I,
)


# ─────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# REGEX ENGINE
# ─────────────────────────────────────────────────────────────

def run_regex(text: str) -> RegexResult:
    r = RegexResult()
    filled = 0
    total = 6

    if m := _RE_ORIGEN.search(text):
        r.origen = m.group(1).strip()
        filled += 1

    if m := _RE_DESTINO.search(text):
        r.destino = m.group(1).strip()
        filled += 1

    if m := _RE_PATENTE.search(text):
        r.patente = m.group(1).upper()
        filled += 1

    if m := _RE_CHOFER.search(text):
        r.chofer = m.group(1).strip()
        filled += 1

    if m := _RE_FECHA.search(text):
        r.fecha = f"{m.group(3)}-{m.group(2):0>2}-{m.group(1):0>2}"
        filled += 1

    if m := _RE_GUIA.search(text):
        r.guia = m.group(1)
        filled += 1

    for m in _RE_ITEM.finditer(text):
        try:
            r.items.append(
                LogisticsItem(
                    cantidad=int(float(m.group(1).replace(",", "."))),
                    unidad=m.group(2),
                    descripcion=m.group(3).strip(),
                )
            )
        except Exception:
            continue

    r.confidence = filled / total
    return r


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def missing_fields(r: RegexResult) -> list[str]:
    fields = []
    if not r.origen:
        fields.append("origen")
    if not r.destino:
        fields.append("destino")
    if not r.patente:
        fields.append("patente")
    if not r.chofer:
        fields.append("chofer")
    if not r.fecha:
        fields.append("fecha")
    if not r.guia:
        fields.append("guia")
    return fields


def to_schema(r: RegexResult) -> ExtractedLogisticsData:
    return ExtractedLogisticsData(
        origen=r.origen,
        destino=r.destino,
        patente_camion=r.patente,
        chofer=r.chofer,
        fecha_despacho=r.fecha,
        numero_guia=r.guia,
        items=r.items,
        observaciones=None,
    )


# ─────────────────────────────────────────────────────────────
# AI FALLBACK (FIXED TYPES)
# ─────────────────────────────────────────────────────────────

async def ai_complete(text: str, r: RegexResult, missing: list[str], settings) -> ExtractedLogisticsData:
    """Complete extraction using OpenAI API for missing fields."""
    from openai import AsyncOpenAI

    if not settings.OPENAI_API_KEY:
        return to_schema(r)

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    input_messages = [
        {
            "role": "system",
            "content": "Extract logistics data. Return only factual information.",
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": f"Missing: {', '.join(missing)}\n\n{text[:2500]}",
                }
            ],
        },
    ]

    resp = await client.responses.parse(
        model=settings.OPENAI_MODEL,
        input=input_messages,
        text_format=ExtractedLogisticsData,
        temperature=0,
    )

    ai = resp.output_parsed or ExtractedLogisticsData()

    return ExtractedLogisticsData(
        origen=r.origen or ai.origen,
        destino=r.destino or ai.destino,
        patente_camion=r.patente or ai.patente_camion,
        chofer=r.chofer or ai.chofer,
        fecha_despacho=r.fecha or ai.fecha_despacho,
        numero_guia=r.guia or ai.numero_guia,
        items=r.items if r.items else ai.items,
        observaciones=ai.observaciones,
    )
# ─────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────

AI_THRESHOLD = 0.7


async def extract_document(file_bytes: bytes, filename: str, content_type: str, settings) -> ExtractedLogisticsData:
    if len(file_bytes) < 20:
        raise ValueError("file too small")

    text = extract_text(file_bytes, content_type)

    if not text:
        logger.info("No text → raw AI fallback")
        return ExtractedLogisticsData()

    r = run_regex(text)
    missing = missing_fields(r)

    if not missing:
        return to_schema(r)

    if r.confidence >= AI_THRESHOLD:
        return to_schema(r)

    return await ai_complete(text, r, missing, settings)