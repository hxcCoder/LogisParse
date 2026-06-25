import re
from typing import Any

from app.services.extractors.base_adapter import BaseAdapter


class StarkenAdapter(BaseAdapter):
    async def extract_data(
        self,
        text: str,
        image_bytes: bytes | None = None,
        settings: Any = None,
        correction_history: list[dict] | None = None,
    ) -> dict[str, Any]:
        # Patrones mejorados:
        # - Origen/Destino: capturan nombres de ciudades con mayúscula y acentos,
        #   máximo 3 palabras
        # - Chofer: nombre y apellido (dos palabras con mayúscula)
        # - Fecha: formato dd/mm/aaaa o aaaa-mm-dd
        # - Guía: número después de "Guía", "GDE", etc.
        # - Patente: evita capturar "GDE-2026" usando negative lookbehind
        patrones = {
            "origen": re.compile(
                r"(?:Origen|Origen Detallado):\s*"
                r"([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,2})",
                re.IGNORECASE,
            ),
            "destino": re.compile(
                r"(?:Destino|Destino Detallado):\s*"
                r"([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,2})",
                re.IGNORECASE,
            ),
            "chofer": re.compile(
                r"(?:Chofer|Conductor):\s*"
                r"([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)",
                re.IGNORECASE,
            ),
            "fecha_despacho": re.compile(
                r"(?:Fecha(?: de Salida)?|FchEmis):\s*"
                r"(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})",
                re.IGNORECASE,
            ),
            "numero_guia": re.compile(
                r"(?:Guía|GUIA|GDE)\s*(?:N°|Nº|Nro\.?)?\s*(\d+)",
                re.IGNORECASE,
            ),
            "patente_camion": re.compile(
                r"(?<!GDE-)([A-Z]{2}-?[A-Z]{2}-?\d{2}|[A-Z]{2}-?\d{4})",
                re.IGNORECASE,
            ),
        }

        extracted = {}
        for key, pattern in patrones.items():
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                extracted[key] = value if value else None
            else:
                extracted[key] = None

        # Si no se encontró origen, intentar buscar con "Desde:" o similar
        if not extracted.get("origen"):
            fallback = re.search(
                r"(?:Desde|Origen):?\s*"
                r"([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,2})",
                text,
                re.IGNORECASE,
            )
            if fallback:
                extracted["origen"] = fallback.group(1).strip()

        extracted["adapter_used"] = "StarkenAdapter"
        return extracted

    def calculate_confidence(self, extracted_data: dict[str, Any]) -> float:
        # Pesos para cada campo (solo si el valor es válido)
        pesos = {
            "origen": 0.15,
            "destino": 0.20,
            "chofer": 0.15,
            "fecha_despacho": 0.15,
            "numero_guia": 0.20,
            "patente_camion": 0.15,
        }
        score = 0.0
        for campo, peso in pesos.items():
            valor = extracted_data.get(campo)
            # Validación simple: no debe ser None, no debe ser string vacío,
            # y para origen/destino no debe tener más de 3 palabras
            if valor and isinstance(valor, str) and len(valor) > 1:
                if campo in ("origen", "destino") and len(valor.split()) > 3:
                    continue
                score += peso * 100
        return min(score, 100.0)
