# app/services/sii_mapper.py
"""
Mapeador de datos para documentos tributarios chilenos (SII).
Extrae RUT emisor, RUT receptor, folio, fecha y monto total
desde texto plano o desde las estructuras de tablas/formularios de AWS Textract.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class SIIMapper:
    """
    Extrae campos específicos del SII chileno desde texto o datos estructurados.
    """

    # ── PATRONES REGEX ──

    # RUT chileno: 12.345.678-K o 12345678-K
    RUT_PATTERN = re.compile(
        r"(?:RUT|R\.U\.T\.?|Rol\s*(?:Único\s*)?Tributario)\s*:?\s*"
        r"(\d{1,2}(?:\.\d{3}){2}-[\dkK])",
        re.IGNORECASE,
    )

    # RUT sin puntos: 12345678-K
    RUT_SIMPLE_PATTERN = re.compile(
        r"\b(\d{7,8}-[\dkK])\b"
    )

    # Folio electrónico SII
    FOLIO_PATTERN = re.compile(
        r"(?:Folio|N[°º]\s*(?:de\s*)?(?:Folio|Documento|Gu[ií]a)?)\s*:?\s*"
        r"(\d{4,})",
        re.IGNORECASE,
    )

    # Fecha en formato dd/mm/aaaa o dd-mm-aaaa
    FECHA_PATTERN = re.compile(
        r"(?:Fecha\s*(?:de\s*)?(?:Emisi[oó]n|Documento|Gu[ií]a)?)\s*:?\s*"
        r"(\d{2}[/-]\d{2}[/-]\d{4})",
        re.IGNORECASE,
    )

    # Monto total (con $, CLP o sin prefijo)
    MONTO_PATTERN = re.compile(
        r"(?:Monto\s*(?:Total|Neto|Bruto)?|Total\s*(?:a\s*Pagar|Factura|Documento)?)\s*:?\s*"
        r"\$?\s*([\d]{1,3}(?:\.[\d]{3})*(?:,\d{2})?)",
        re.IGNORECASE,
    )

    # Patente de camión chilena
    PATENTE_PATTERN = re.compile(
        r"(?:Patente|PPU)\s*(?:Veh[ií]culo|Cami[oó]n)?\s*:?\s*"
        r"([A-Z]{2,4}[\s-]?\d{2,4})",
        re.IGNORECASE,
    )

    def extract_from_text(self, text: str) -> dict[str, Any]:
        """
        Extrae campos SII desde texto plano (OCR o Textract).

        Args:
            text: Texto extraído del documento.

        Returns:
            Diccionario con los campos mapeados.
        """
        clean = re.sub(r"\s+", " ", text).strip()
        result: dict[str, Any] = {}

        # 1. RUT Emisor (primer RUT encontrado)
        rut_match = self.RUT_PATTERN.search(clean)
        if rut_match:
            result["rut_emisor"] = self._normalize_rut(rut_match.group(1))
        else:
            # Buscar RUTs simples y tomar el primero como emisor
            ruts = self.RUT_SIMPLE_PATTERN.findall(clean)
            if ruts:
                result["rut_emisor"] = self._normalize_rut(ruts[0])

        # 2. RUT Receptor (segundo RUT encontrado)
        if not rut_match:
            # Buscar todos los RUTs y tomar el segundo
            ruts = self.RUT_SIMPLE_PATTERN.findall(clean)
            if len(ruts) >= 2:
                result["rut_receptor"] = self._normalize_rut(ruts[1])
        else:
            # Buscar después del primer RUT
            remaining = clean[rut_match.end():]
            rut2 = self.RUT_SIMPLE_PATTERN.search(remaining)
            if rut2:
                result["rut_receptor"] = self._normalize_rut(rut2.group(1))

        # 3. Folio SII
        folio_match = self.FOLIO_PATTERN.search(clean)
        if folio_match:
            result["folio_sii"] = folio_match.group(1)

        # 4. Fecha de emisión
        fecha_match = self.FECHA_PATTERN.search(clean)
        if fecha_match:
            result["fecha_emision"] = self._normalize_date(fecha_match.group(1))

        # 5. Monto total
        monto_match = self.MONTO_PATTERN.search(clean)
        if monto_match:
            result["monto_total"] = self._normalize_monto(monto_match.group(1))

        # 6. Patente
        patente_match = self.PATENTE_PATTERN.search(clean)
        if patente_match:
            result["patente_camion"] = patente_match.group(1).upper().replace(" ", "")

        logger.info(
            "Mapeo SII completado: RUTs=%s, Folio=%s, Fecha=%s, Monto=%s",
            "✓" if result.get("rut_emisor") else "✗",
            "✓" if result.get("folio_sii") else "✗",
            "✓" if result.get("fecha_emision") else "✗",
            "✓" if result.get("monto_total") else "✗",
        )
        return result

    def extract_from_textract_response(
        self, textract_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Extrae campos SII desde la respuesta estructurada de AWS Textract
        (tablas y formularios).

        Args:
            textract_data: Diccionario con 'tables' y 'forms' de Textract.

        Returns:
            Diccionario con los campos mapeados.
        """
        result: dict[str, Any] = {}

        # 1. Intentar extraer de formularios (clave-valor)
        forms = textract_data.get("forms", {})
        for key, value in forms.items():
            key_lower = key.lower()

            if any(kw in key_lower for kw in ["rut emisor", "rut proveedor", "rut vendedor"]):
                rut = self.RUT_SIMPLE_PATTERN.search(value)
                if rut:
                    result["rut_emisor"] = self._normalize_rut(rut.group(1))

            elif any(kw in key_lower for kw in ["rut receptor", "rut cliente", "rut comprador"]):
                rut = self.RUT_SIMPLE_PATTERN.search(value)
                if rut:
                    result["rut_receptor"] = self._normalize_rut(rut.group(1))

            elif any(kw in key_lower for kw in ["folio", "n° documento", "número"]):
                result["folio_sii"] = value.strip()

            elif any(kw in key_lower for kw in ["fecha emisión", "fecha documento"]):
                result["fecha_emision"] = self._normalize_date(value)

            elif any(kw in key_lower for kw in ["monto total", "total", "total a pagar"]):
                result["monto_total"] = self._normalize_monto(value)

        # 2. Si no se encontró en formularios, buscar en tablas
        tables = textract_data.get("tables", [])
        for table in tables:
            rows = table.get("rows", [])
            for row in rows:
                row_text = " ".join(str(cell) for cell in row)

                # Buscar RUTs en cada fila
                if not result.get("rut_emisor"):
                    rut_match = self.RUT_PATTERN.search(row_text)
                    if rut_match:
                        result["rut_emisor"] = self._normalize_rut(rut_match.group(1))

                if not result.get("folio_sii"):
                    folio_match = self.FOLIO_PATTERN.search(row_text)
                    if folio_match:
                        result["folio_sii"] = folio_match.group(1)

                if not result.get("monto_total"):
                    monto_match = self.MONTO_PATTERN.search(row_text)
                    if monto_match:
                        result["monto_total"] = self._normalize_monto(
                            monto_match.group(1)
                        )

        logger.info(
            "Mapeo desde Textract completado: %d campos encontrados.",
            len(result),
        )
        return result

    # ── NORMALIZADORES ──

    @staticmethod
    def _normalize_rut(rut: str) -> str:
        """
        Normaliza un RUT chileno al formato estándar: 12.345.678-K

        Args:
            rut: RUT en cualquier formato (12345678-k, 12.345.678-K, etc.)

        Returns:
            RUT normalizado con puntos y guión, dígito verificador en mayúscula.
        """
        # Limpiar caracteres no relevantes
        clean = re.sub(r"[^\dkK]", "", rut.upper())

        if len(clean) < 8:
            return rut  # No se puede normalizar

        dv = clean[-1]
        numeros = clean[:-1]

        # Formatear con puntos
        if len(numeros) == 8:
            formatted = f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:]}-{dv}"
        elif len(numeros) == 7:
            formatted = f"{numeros[0]}.{numeros[1:4]}.{numeros[4:]}-{dv}"
        else:
            formatted = f"{numeros}-{dv}"

        return formatted

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """
        Normaliza una fecha a formato dd/mm/aaaa.

        Args:
            date_str: Fecha en cualquier formato (dd/mm/aaaa, dd-mm-aaaa, etc.)

        Returns:
            Fecha en formato dd/mm/aaaa.
        """
        # Si ya está en dd/mm/aaaa, devolver tal cual
        if re.match(r"^\d{2}/\d{2}/\d{4}$", date_str):
            return date_str

        # Si está en dd-mm-aaaa, convertir
        match = re.match(r"^(\d{2})-(\d{2})-(\d{4})$", date_str)
        if match:
            return f"{match.group(1)}/{match.group(2)}/{match.group(3)}"

        return date_str

    @staticmethod
    def _normalize_monto(monto_str: str) -> str:
        """
        Normaliza un monto a formato numérico limpio.

        Args:
            monto_str: Monto en cualquier formato ($1.234.567,89, 1234567, etc.)

        Returns:
            Monto como string numérico (ej: "1234567").
        """
        # Eliminar símbolos de moneda y separadores
        clean = re.sub(r"[\$\.\s]", "", monto_str)
        # Reemplazar coma decimal por punto
        clean = clean.replace(",", ".")
        return clean


# ── FUNCIÓN DE CONVENIENCIA ──

def map_sii_data(
    text: str,
    textract_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Mapea los datos SII desde texto y/o respuesta de Textract.

    Args:
        text: Texto extraído del documento.
        textract_data: Respuesta estructurada de AWS Textract (opcional).

    Returns:
        Diccionario con los campos SII mapeados.
    """
    mapper = SIIMapper()
    result = mapper.extract_from_text(text)

    if textract_data:
        textract_result = mapper.extract_from_textract_response(textract_data)
        # Fusionar: los datos de formularios/tablas tienen prioridad
        result.update({k: v for k, v in textract_result.items() if v})

    return result