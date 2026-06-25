"""
Orquestador de extracción para LogisParse SaaS.
1. Extrae texto crudo (OCR / PDF).
2. Limpia el texto (elimina basura de tablas, encabezados, etc.).
3. Delega al AdapterFactory para enrutamiento inteligente.
4. Valida semánticamente los campos extraídos.
5. Soporta aprendizaje continuo a través de correction_history.
"""

import logging
import re
from io import BytesIO
from typing import Any

from app.core.config import Settings
from app.schemas.extraction import ExtractedLogisticsData
from app.services.extractors.adapter_factory import AdapterFactory
from app.services.extractors.generic_llm_adapter import GenericLLMAdapter

logger = logging.getLogger(__name__)


# ----------------------------------------------
# LIMPIEZA DE TEXTO
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
        # Saltar líneas que son solo números, guiones, barras, etc.
        if re.match(r"^[\d\s\-\/\.\,\%\$]+$", line):
            continue
        # Saltar líneas en mayúsculas que parecen encabezados de tabla (más de 4 letras mayúsculas)
        if re.match(r"^[A-Z\s]{5,}$", line):
            continue
        # Saltar líneas que empiezan con "PAGO CON", "CONCEPTO", etc.
        if re.match(r"^(PAGO|CONCEPTO|PORCENTAJE|CÁLCULO|RETENCIONES)", line, re.IGNORECASE):
            continue
        # Saltar líneas que son etiquetas de tabla como "Seguro Invalidez..."
        if ":" not in line and len(line.split()) > 5:
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


# ----------------------------------------------
# VALIDACIÓN SEMÁNTICA DE CAMPOS
# ----------------------------------------------
def validate_extracted_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Valida cada campo extraído y lo deja como None si no cumple con el formato esperado.
    """
    def normalize_city(name: str) -> str:
        return " ".join(word.capitalize() for word in name.lower().split())

    validated = {}

    for campo, valor in data.items():
        if not valor or not isinstance(valor, str) or len(valor.strip()) < 2:
            validated[campo] = None
            continue

        valor = valor.strip()

        if campo in ("origen", "destino"):
            # Debe ser un nombre de ciudad (solo letras y espacios, no más de 3 palabras)
            if re.match(r"^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,2}$", valor):
                validated[campo] = normalize_city(valor)
            else:
                validated[campo] = None

        elif campo == "chofer":
            # Debe ser nombre y apellido (dos palabras con mayúscula)
            if re.match(r"^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+$", valor):
                validated[campo] = valor
            else:
                validated[campo] = None

        elif campo == "fecha_despacho":
            # Formato dd/mm/aaaa o aaaa-mm-dd
            if re.match(r"^\d{2}/\d{2}/\d{4}$", valor) or re.match(r"^\d{4}-\d{2}-\d{2}$", valor):
                validated[campo] = valor
            else:
                validated[campo] = None

        elif campo == "numero_guia":
            # Solo números
            if re.match(r"^\d+$", valor):
                validated[campo] = valor
            else:
                validated[campo] = None

        elif campo == "patente_camion":
            # Formato XX-XX-12 o XX-1234 (o sin guiones)
            if re.match(r"^[A-Z]{2}-?[A-Z]{2}-?\d{2}$", valor) or re.match(
                r"^[A-Z]{2}-?\d{4}$", valor
            ):
                validated[campo] = valor.upper()
            else:
                validated[campo] = None

        else:
            # Otros campos: se pasan tal cual
            validated[campo] = valor

    return validated


# ----------------------------------------------
# EXTRACCIÓN DE TEXTO
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
    if content_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    if content_type in ("image/png", "image/jpeg", "image/jpg"):
        return extract_text_from_image(file_bytes)
    return ""


# ----------------------------------------------
# ORQUESTADOR PRINCIPAL
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

    # 1. Extraer texto crudo
    text = extract_text(file_bytes, content_type)
    if not text:
        logger.info("No text extracted from %s", filename)
        return ExtractedLogisticsData(confidence_score=0.0, adapter_used="None")

    # 2. Limpiar el texto (eliminar ruido)
    cleaned_text = clean_extracted_text(text)
    logger.debug("Texto limpio (primeros 200 chars): %s", cleaned_text[:200])

    # 3. Obtener adaptador según clasificación
    adapter = AdapterFactory.get_adapter(cleaned_text)

    # 4. Extracción inicial
    raw_data = await adapter.extract_data(
        cleaned_text,
        image_bytes=file_bytes,
        settings=settings,
        correction_history=correction_history,
    )

    # 5. Validación semántica de los campos extraídos
    raw_data = validate_extracted_data(raw_data)

    # 6. Calcular confianza
    score = adapter.calculate_confidence(raw_data)

    # 7. Si confianza baja o faltan críticos, enriquecer con IA
    campos_criticos = ["numero_guia", "patente_camion"]
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

        # Fusionar: los valores de la IA solo se usan si el adaptador específico no los tiene
        for key, value in ai_data.items():
            valor_actual = raw_data.get(key)
            if not valor_actual or (
                isinstance(valor_actual, str) and len(valor_actual.split()) > 3
            ):
                if isinstance(value, str) and len(value.split()) > 3:
                    continue
                raw_data[key] = value

        # Re-validar después de la fusión
        raw_data = validate_extracted_data(raw_data)

        raw_data["adapter_used"] = f"{adapter.__class__.__name__} + GenericLLM"
        score = adapter.calculate_confidence(raw_data)
        raw_data["confidence_score"] = score
        logger.info("Confianza después de enriquecimiento: %s", score)
    else:
        raw_data["confidence_score"] = score
        if "adapter_used" not in raw_data:
            raw_data["adapter_used"] = adapter.__class__.__name__

    logger.info(
        "Extracción finalizada. Adaptador: %s | Confianza: %s", raw_data.get("adapter_used"), score
    )

    return ExtractedLogisticsData(**raw_data)