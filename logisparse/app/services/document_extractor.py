# app/services/document_extractor.py
"""
Orquestador de extracción para LogisParse SaaS.
Flujo completo:
1. Extrae texto con AWS Textract (tablas + formularios) o fallback OCR local
2. Mapea campos SII chilenos (RUT, folio, fecha, monto)
3. Enriquece con adaptadores existentes (Starken, Guía, LLM)
4. Valida semánticamente
5. Genera Excel automáticamente
6. Mueve archivo a /procesados para bandeja limpia
"""

import logging
import re
from datetime import datetime
from io import BytesIO
from typing import Any

from app.core.config import Settings
from app.schemas.extraction import ExtractedLogisticsData
from app.services.aws_textract_service import create_textract_service
from app.services.excel_service import generate_excel_report
from app.services.extractors.adapter_factory import AdapterFactory
from app.services.extractors.generic_llm_adapter import GenericLLMAdapter
from app.services.file_manager import create_file_manager
from app.services.sii_mapper import map_sii_data

logger = logging.getLogger(__name__)

# ----------------------------------------------
# LIMPIEZA DE TEXTO (existente)
# ----------------------------------------------
def clean_extracted_text(text: str) -> str:
    """
    Elimina líneas que parecen ruido: encabezados de tabla, líneas con solo números,
    líneas con mayúsculas sostenidas (ej. "CONCEPTO", "PORCENTAJE"), etc.
    """
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r"^[\d\s\-\/\.\,\%\$]+$", line):
            continue
        if re.match(r"^[A-Z\s]{5,}$", line):
            continue
        if re.match(r"^(PAGO|CONCEPTO|PORCENTAJE|CÁLCULO|RETENCIONES)", line, re.IGNORECASE):
            continue
        if ":" not in line and len(line.split()) > 5:
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


# ----------------------------------------------
# VALIDACIÓN SEMÁNTICA (existente)
# ----------------------------------------------
def validate_extracted_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Valida cada campo extraído y lo deja como None si no cumple con el formato esperado.
    """

    def normalize_city(name: str) -> str:
        return " ".join(word.capitalize() for word in name.lower().split())

    validated: dict[str, Any] = {}

    for campo, valor in data.items():
        if not valor or not isinstance(valor, str) or len(valor.strip()) < 2:
            validated[campo] = None
            continue

        valor = valor.strip()

        if campo in ("origen", "destino"):
            if re.match(r"^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,2}$", valor):
                validated[campo] = normalize_city(valor)
            else:
                validated[campo] = None

        elif campo == "chofer":
            if re.match(r"^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+$", valor):
                validated[campo] = valor
            else:
                validated[campo] = None

        elif campo == "fecha_despacho":
            if re.match(r"^\d{2}[/-]\d{2}[/-]\d{4}$", valor):
                if "-" in valor:
                    partes = valor.split("-")
                    valor = f"{partes[0]}/{partes[1]}/{partes[2]}"
                validated[campo] = valor
            else:
                validated[campo] = None

        elif campo == "numero_guia":
            if re.match(r"^\d+$", valor):
                validated[campo] = valor
            else:
                validated[campo] = None

        elif campo == "patente_camion":
            if re.match(r"^[A-Z]{2}-?[A-Z]{2}-?\d{2}$", valor) or re.match(
                r"^[A-Z]{2}-?\d{4}$", valor
            ):
                validated[campo] = valor.upper()
            else:
                validated[campo] = None

        else:
            validated[campo] = valor

    return validated


# ----------------------------------------------
# EXTRACCIÓN LOCAL (fallback)
# ----------------------------------------------
def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        import pdfplumber
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
        import pytesseract
        from PIL import Image
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
    """Extracción local (fallback) según el tipo de contenido."""
    if content_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    if content_type in ("image/png", "image/jpeg", "image/jpg"):
        return extract_text_from_image(file_bytes)
    return ""


# ----------------------------------------------
# EXTRACCIÓN CON AWS TEXTRACT (NUEVO)
# ----------------------------------------------
def extract_text_with_textract(
    file_bytes: bytes,
    content_type: str,
) -> tuple[str, dict[str, Any]]:
    """
    Intenta extraer texto y estructuras (tablas/formularios) usando AWS Textract.
    Si falla, vuelve automáticamente al OCR local.

    Returns:
        Tupla (texto_plano, datos_estructurados)
    """
    try:
        textract = create_textract_service()
        text = textract.extract_text(file_bytes)
        structures = textract.extract_tables_and_forms(file_bytes)
        logger.info("Textract extrajo %d caracteres de texto plano.", len(text))
        logger.info(
            "Textract encontró %d tablas y %d campos de formulario.",
            len(structures.get("tables", [])),
            len(structures.get("forms", {})),
        )
        return text, structures
    except Exception as exc:
        logger.warning("AWS Textract falló (%s). Usando OCR local.", exc)
        # Fallback a extracción local
        text = extract_text(file_bytes, content_type)
        return text, {}


# ----------------------------------------------
# ORQUESTADOR PRINCIPAL (ACTUALIZADO)
# ----------------------------------------------
async def extract_document(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    settings: Settings,
    correction_history: list[dict] | None = None,
) -> ExtractedLogisticsData:

    if len(file_bytes) < 20:
        raise ValueError("file too small")

    # ═══════════════════════════════════════════════
    # 1. Extraer texto con Textract + fallback local
    # ═══════════════════════════════════════════════
    text, textract_data = extract_text_with_textract(file_bytes, content_type)

    if not text:
        logger.info("No se extrajo texto de %s", filename)
        return ExtractedLogisticsData(confidence_score=0.0, adapter_used="None")

    # 2. Limpiar el texto (eliminar ruido)
    cleaned_text = clean_extracted_text(text)
    logger.debug("Texto limpio (primeros 200 chars): %s", cleaned_text[:200])

    # ═══════════════════════════════════════════════
    # 3. Mapeo de campos SII chilenos (NUEVO)
    # ═══════════════════════════════════════════════
    sii_data = map_sii_data(cleaned_text, textract_data)
    logger.info("Campos SII mapeados: %s", sii_data)

    # ═══════════════════════════════════════════════
    # 4. Adaptador específico (existente)
    # ═══════════════════════════════════════════════
    adapter = AdapterFactory.get_adapter(cleaned_text)

    raw_data = await adapter.extract_data(
        cleaned_text,
        image_bytes=file_bytes,
        settings=settings,
        correction_history=correction_history,
    )

    # 5. Validación semántica de los campos extraídos
    raw_data = validate_extracted_data(raw_data)

    # ═══════════════════════════════════════════════
    # 6. Fusión: los datos SII tienen prioridad
    # ═══════════════════════════════════════════════
    for key, value in sii_data.items():
        if value and not raw_data.get(key):
            raw_data[key] = value

    # 7. Calcular confianza inicial
    score = adapter.calculate_confidence(raw_data)

    # 8. Enriquecer con IA si confianza baja o faltan campos críticos
    campos_criticos = [
        "numero_guia", "patente_camion",
        "rut_emisor", "folio_sii",   # añadidos para el flujo SII
    ]
    faltan_criticos = any(not raw_data.get(campo) for campo in campos_criticos)

    if (score < 70 or faltan_criticos) and not isinstance(adapter, GenericLLMAdapter):
        logger.info("Confianza baja (%s) o faltan críticos. Enriqueciendo con IA genérica.", score)
        generic_adapter = GenericLLMAdapter()
        ai_data = await generic_adapter.extract_data(
            cleaned_text,
            image_bytes=file_bytes,
            settings=settings,
            correction_history=correction_history,
        )

        # Fusionar IA solo donde el adaptador no tenga valor o el valor sea sospechoso
        for key, value in ai_data.items():
            valor_actual = raw_data.get(key)
            if not valor_actual or (
                isinstance(valor_actual, str) and len(valor_actual.split()) > 3
            ):
                if isinstance(value, str) and len(value.split()) > 3:
                    continue
                raw_data[key] = value

        raw_data = validate_extracted_data(raw_data)
        raw_data["adapter_used"] = f"{adapter.__class__.__name__} + GenericLLM"
        score = adapter.calculate_confidence(raw_data)
        raw_data["confidence_score"] = score
    else:
        raw_data["confidence_score"] = score
        if "adapter_used" not in raw_data:
            raw_data["adapter_used"] = adapter.__class__.__name__

    # ═══════════════════════════════════════════════
    # 9. Extraer número de guía del nombre del archivo
    # ═══════════════════════════════════════════════
    if not raw_data.get("numero_guia") and filename:
        match = re.search(r"GDE[- ]?(\d{4}[- ]?\d+)", filename, re.IGNORECASE)
        if match:
            raw_data["numero_guia"] = match.group(1).replace(" ", "").replace("-", "")
            logger.info("Número de guía extraído del archivo: %s", raw_data["numero_guia"])
            score = adapter.calculate_confidence(raw_data)
            raw_data["confidence_score"] = score

    # ═══════════════════════════════════════════════
    # 10. Generar Excel automáticamente (NUEVO)
    # ═══════════════════════════════════════════════
    try:
        excel_bytes = generate_excel_report(
            [raw_data],
            output_path=f"procesados/excel/{filename}.xlsx",
        )
        logger.info("Excel generado (%d bytes) para %s", len(excel_bytes), filename)
    except Exception:
        logger.exception("Error generando Excel para %s", filename)

    # ═══════════════════════════════════════════════
    # 11. Mover archivo original a /procesados (NUEVO)
    # ═══════════════════════════════════════════════
    try:
        file_manager = create_file_manager()
        saved_path = file_manager.save_uploaded_file(file_bytes, filename)
        processed_path = file_manager.move_to_processed(
            saved_path,
            subfolder=datetime.now().strftime("%Y/%m/%d"),
        )
        logger.info("Archivo original archivado en: %s", processed_path)
    except Exception:
        logger.exception("Error al archivar el documento %s", filename)

    logger.info(
        "Extracción finalizada. Adaptador: %s | Confianza: %s",
        raw_data.get("adapter_used"),
        raw_data.get("confidence_score"),
    )

    return ExtractedLogisticsData(**raw_data)