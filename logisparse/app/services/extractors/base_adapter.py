# app/services/extractors/base_adapter.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAdapter(ABC):
    """Interfaz base asíncrona para extractores."""
    
    @abstractmethod
    async def extract_data(self, text: str, image_bytes: bytes | None = None, settings: Any = None) -> Dict[str, Any]:
        """Extrae la información logística del documento de forma asíncrona."""
        pass

    @abstractmethod
    def calculate_confidence(self, extracted_data: Dict[str, Any]) -> float:
        """Calcula el puntaje de confianza (0-100) de la extracción."""
        pass