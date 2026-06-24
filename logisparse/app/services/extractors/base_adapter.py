from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAdapter(ABC):
    @abstractmethod
    async def extract_data(
        self,
        text: str,
        image_bytes: bytes | None = None,
        settings: Any = None,
        correction_history: list[dict] | None = None,   # <-- AÑADIR
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def calculate_confidence(self, extracted_data: Dict[str, Any]) -> float:
        pass