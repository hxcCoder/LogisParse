# app/services/extractors/adapter_factory.py
from app.services.extractors.base_adapter import BaseAdapter
from app.services.extractors.generic_llm_adapter import GenericLLMAdapter
from app.services.extractors.specific.starken_adapter import StarkenAdapter


class DocumentClassifier:
    @staticmethod
    def identify_company(text: str) -> str:
        """Clasificador rudimentario. En el futuro puede ser un modelo ML pequeño."""
        text_upper = text.upper()
        if "STARKEN" in text_upper or "TURBUS" in text_upper:
            return "starken"
        # Si no detecta nada conocido...
        return "unknown"


class AdapterFactory:
    @staticmethod
    def get_adapter(text: str) -> BaseAdapter:
        # 1. Primero clasificamos
        company_id = DocumentClassifier.identify_company(text)

        # 2. Seleccionamos el adaptador correcto
        adapters = {
            "starken": StarkenAdapter(),
            # "ccu": CCUAdapter(),
            # "dhl": DHLAdapter(),
        }

        # Si la empresa existe en el diccionario, retorna ese adaptador.
        # Si no ('unknown'), retorna el GenericLLMAdapter.
        return adapters.get(company_id, GenericLLMAdapter())
