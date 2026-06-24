# app/services/document_extractor.py
"""
Orquestador de extracción para LogisParse SaaS.
1. Extrae texto crudo (OCR / PDF).
2. Delega al AdapterFactory para enrutamiento inteligente (RegEx Específico o IA Generativa).
"""

import logging
from io import BytesIO

from app.core.config import Settings
from app.schemas.extraction import ExtractedLogisticsData
from app.services.extractors.adapter_factory import AdapterFactory

logger = logging.getLogger(__name__)

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
        return pytesseract.image_to_string(img, lang="spa")
    except Exception:
        logger.exception("Image OCR failed")
        return ""

def extract_text(file_bytes: bytes, content_type: str) -> str:
    if content_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    if content_type in ("image/png", "image/jpeg", "image/jpg"):
        return extract_text_from_image(file_bytes)
    return ""

async def extract_document(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    settings: Settings,
) -> ExtractedLogisticsData:
    
    if len(file_bytes) < 20:
        raise ValueError("file too small")

    # 1. OCR Crudo (Manteniendo tu lógica original)
    text = extract_text(file_bytes, content_type)
    if not text:
        logger.info("No text extracted from %s", filename)
        return ExtractedLogisticsData(confidence_score=0.0, adapter_used="None")

    # 2. Orquestación SaaS: El Factory decide quién lo procesa
    adapter = AdapterFactory.get_adapter(text)

    # 3. Extracción (Ahora es asíncrono para soportar llamadas a la API de OpenAI)
    raw_data = await adapter.extract_data(text, image_bytes=file_bytes, settings=settings)

    # 4. Auditoría y Confianza
    score = adapter.calculate_confidence(raw_data)
    raw_data["confidence_score"] = score
    
    logger.info("Extracción finalizada. Adaptador: %s | Confianza: %s", raw_data.get("adapter_used"), score)

    # Convertimos al Schema dinámico
    return ExtractedLogisticsData(**raw_data)