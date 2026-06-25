from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    @abstractmethod
    async def extract_data(
        self,
        text: str,
        image_bytes: bytes | None = None,
        settings: Any = None,
        correction_history: list[dict] | None = None,  # <-- AÑADIR
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    def calculate_confidence(self, extracted_data: dict[str, Any]) -> float:
        pass
