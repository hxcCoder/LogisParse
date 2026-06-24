# app/services/extractors/specific/starken_adapter.py
import re
from typing import Dict, Any
from app.services.extractors.base_adapter import BaseAdapter

class StarkenAdapter(BaseAdapter):
    
    # AGREGAMOS ASYNC Y SETTINGS PARA CUMPLIR LA INTERFAZ
    async def extract_data(self, text: str, image_bytes: bytes | None = None, settings: Any = None) -> Dict[str, Any]:
        # Usamos Regex para buscar patrones exactos (ej. Patente chilena: XX-XX-11)
        patente_match = re.search(r'([A-Z]{2}-?[A-Z]{2}-?\d{2}|[A-Z]{2}-?\d{4})', text)
        guia_match = re.search(r'GUIA N°\s*(\d+)', text)
        
        return {
            "origen": "Centro Distribución Starken",
            "patente_camion": patente_match.group(0) if patente_match else None,
            "numero_guia": guia_match.group(1) if guia_match else None,
            "adapter_used": "StarkenAdapter"
        }

    def calculate_confidence(self, extracted_data: Dict[str, Any]) -> float:
        score = 100.0
        # Penalizamos si faltan datos críticos
        if not extracted_data.get("patente_camion"):
            score -= 30.0
        if not extracted_data.get("numero_guia"):
            score -= 40.0
        return max(score, 0.0)