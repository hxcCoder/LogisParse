# app/services/extractors/adapter_factory.py

"""
Adapter Factory para LogisParse.
Clasifica documentos según su contenido y asigna el adaptador más adecuado.
Estrategia de fallback: si no se reconoce ningún formato, usa IA genérica.
"""

import logging
import re

from app.services.extractors.base_adapter import BaseAdapter
from app.services.extractors.generic_llm_adapter import GenericLLMAdapter
from app.services.extractors.specific.chilean_guia_adapter import ChileanGuiaAdapter
from app.services.extractors.specific.starken_adapter import StarkenAdapter

logger = logging.getLogger(__name__)


class DocumentClassifier:
    @staticmethod
    def identify_company(text: str) -> str:
        text_upper = text.upper()

        # ---- DEPURACIÓN ----
        logger.debug(f"🔍 Texto a clasificar (primeros 500 chars): {text[:500]}")

        # 1. DETECTAR GUÍA DE DESPACHO (PRIORIDAD ALTA)
        # Palabras clave
        keywords = [
            "GDE",
            "GUIA DE DESPACHO",
            "GUÍA DE DESPACHO",
            "FOLIO ELECTRONICO SII",
            "FOLIO ELECTRÓNICO SII",
        ]
        for kw in keywords:
            if kw in text_upper:
                return "chilean_guia"

        # Patrón GDE-YYYY-NNNNN
        if re.search(r'GDE\s*[-:]?\s*\d{4}\s*[-:]?\s*\d+', text_upper):
            return "chilean_guia"

        # Combinación de campos típicos
        has_patente = re.search(r'PATENTE\s*VEH[IÍ]CULO', text_upper) is not None
        has_chofer = re.search(r'CHOFER', text_upper) is not None
        has_fecha_emision = re.search(r'FECHA\s*EMISI[ÓO]N', text_upper) is not None
        has_transportista = re.search(r'TRANSPORTISTA', text_upper) is not None
        has_origen_destino = re.search(r'DIRECCI[ÓO]N\s*DE\s*ORIGEN', text_upper) is not None

        if (
            sum([has_patente, has_chofer, has_fecha_emision, has_transportista, has_origen_destino])
            >= 3
        ):
            return "chilean_guia"

        # 2. DETECTAR STARKEN (solo si NO es guía)
        if "STARKEN" in text_upper or "TURBUS" in text_upper:
            return "starken"

        # 3. Si no, devolver unknown
        return "unknown"


class AdapterFactory:
    @staticmethod
    def get_adapter(text: str) -> BaseAdapter:
        company_id = DocumentClassifier.identify_company(text)

        adapters = {
            "starken": StarkenAdapter(),
            "chilean_guia": ChileanGuiaAdapter(),
        }

        if company_id in adapters:
            logger.info(
                f"📌 Clasificado como '{company_id}' → "
                f"usando {adapters[company_id].__class__.__name__}"
            )
            return adapters[company_id]

        logger.info(
            f"❓ Documento no clasificado (tipo '{company_id}') → usando GenericLLMAdapter"
        )
        return GenericLLMAdapter()