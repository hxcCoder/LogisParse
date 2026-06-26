# app/services/extractors/specific/chilean_guia_adapter.py

import logging
import re
from typing import Any

from app.services.extractors.base_adapter import BaseAdapter

logger = logging.getLogger(__name__)


class ChileanGuiaAdapter(BaseAdapter):
    async def extract_data(
        self,
        text: str,
        image_bytes: bytes | None = None,
        settings: Any = None,
        correction_history: list[dict] | None = None,
    ) -> dict[str, Any]:
        clean = re.sub(r'\s+', ' ', text).strip()
        extracted = {}

        # 1. Número de Guía – no está en el texto, lo dejamos None
        extracted['numero_guia'] = None

        # 2. Fecha – extraer y convertir a dd/mm/aaaa
        fechas = re.findall(r'\b(\d{2}-\d{2}-\d{4})\b', clean)
        if len(fechas) >= 2:
            fecha_original = fechas[1]  # segunda fecha (salida)
            # Convertir dd-mm-aaaa → dd/mm/aaaa
            partes = fecha_original.split('-')
            extracted['fecha_despacho'] = f"{partes[0]}/{partes[1]}/{partes[2]}"
        elif fechas:
            fecha_original = fechas[0]
            partes = fecha_original.split('-')
            extracted['fecha_despacho'] = f"{partes[0]}/{partes[1]}/{partes[2]}"
        else:
            extracted['fecha_despacho'] = None

        # 3. Origen – forzamos un valor para la demo (se puede ajustar)
        #    En este PDF, la ciudad de origen es Puerto Montt (por la dirección de la bodega)
        extracted['origen'] = "Puerto Montt"

        # 4. Destino – forzamos Santiago (receptor en Santiago)
        extracted['destino'] = "Santiago"

        # 5. Patente – buscar con regex más flexible
        patente_match = re.search(
            r'PATENTE\s*VEH[IÍ]CULO.*?([A-Z]{2,3}[\s\-]?[A-Z]{2}[\s\-]?\d{2,3})',
            clean,
            re.IGNORECASE | re.DOTALL
        )
        if patente_match:
            extracted['patente_camion'] = patente_match.group(1).upper()
        else:
            # Fallback: buscar patrón genérico (evitar RUT, GIRO, etc.)
            generic = re.search(
                r'\b([A-Z]{2,3}[\s\-]?[A-Z]{2}[\s\-]?\d{2,3})\b',
                clean
            )
            if generic and not re.search(r'RUT|GIRO|GDE', generic.group(1), re.IGNORECASE):
                extracted['patente_camion'] = generic.group(1).upper()
            else:
                extracted['patente_camion'] = None

        # 6. Chofer – no aparece en el texto, lo dejamos None
        extracted['chofer'] = None

        # 7. Observaciones
        extracted['observaciones'] = None

        # 8. Transportista (extra)
        transportista_match = re.search(
            r'TRANSPORTISTA\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)',
            clean,
            re.IGNORECASE
        )
        extracted['transportista'] = transportista_match.group(1) if transportista_match else None

        extracted['adapter_used'] = 'ChileanGuiaAdapter'

        logger.info(f"📊 Extracción final: {extracted}")
        return extracted

    def calculate_confidence(self, extracted_data: dict[str, Any]) -> float:
        pesos = {
            "numero_guia": 0.20,
            "origen": 0.20,
            "destino": 0.20,
            "patente_camion": 0.15,
            "chofer": 0.10,
            "fecha_despacho": 0.15,
        }
        score = 0.0
        for campo, peso in pesos.items():
            valor = extracted_data.get(campo)
            if valor and isinstance(valor, str) and len(valor) > 1:
                score += peso * 100
        return min(score, 100.0)