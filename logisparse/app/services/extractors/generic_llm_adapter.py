# app/services/extractors/generic_llm_adapter.py
from typing import Dict, Any
import logging
from app.services.extractors.base_adapter import BaseAdapter
from app.schemas.extraction import ExtractedLogisticsData

logger = logging.getLogger(__name__)

class GenericLLMAdapter(BaseAdapter):
    
    async def extract_data(self, text: str, image_bytes: bytes | None = None, settings: Any = None) -> Dict[str, Any]:
        """Utiliza OpenAI Structured Outputs para extraer datos de formatos desconocidos."""
        from openai import AsyncOpenAI
        
        # Fallback en caso de que no haya API Key configurada
        if not settings or not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY no encontrada. Devolviendo JSON mockeado.")
            return {
                "origen": "Desconocido",
                "destino": "Desconocido",
                "adapter_used": "GenericLLMAdapter (Fallo API)"
            }

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # FIX 1: Tipamos la lista explícitamente como list[Any] para satisfacer los
        # estrictos TypedDicts de la librería de OpenAI.
        input_messages: list[Any] = [
            {
                "role": "system",
                "content": (
                    "Eres un experto verificando documentos de logística y tributarios chilenos. "
                    "Extrae los datos solicitados. Devuelve solo información factual presente en el texto."
                ),
            },
            {
                "role": "user",
                "content": f"Texto del documento:\n{text[:2000]}", 
            },
        ]

        try:
            response = await client.beta.chat.completions.parse(
                model=settings.OPENAI_MODEL,
                messages=input_messages,
                response_format=ExtractedLogisticsData,
                temperature=0,
            )
            
            # FIX 2: Verificamos que 'parsed' no sea None antes de usar model_dump()
            parsed_data = response.choices[0].message.parsed
            
            if not parsed_data:
                logger.error("OpenAI falló al estructurar la respuesta (parsed es None).")
                return {"adapter_used": "GenericLLMAdapter (Error de Parseo)"}
            
            # Ahora Pylance sabe que parsed_data es seguro de usar
            ai_data = parsed_data.model_dump()
            ai_data["adapter_used"] = "GenericLLMAdapter (OpenAI)"
            
            return ai_data
            
        except Exception as e:
            logger.exception("Fallo en la llamada a OpenAI")
            return {"adapter_used": f"GenericLLMAdapter (Error: {str(e)})"}

    def calculate_confidence(self, extracted_data: Dict[str, Any]) -> float:
        score = 85.0 
        
        if not extracted_data.get("patente_camion"):
            score -= 20.0
        if not extracted_data.get("numero_guia"):
            score -= 20.0
            
        return max(score, 0.0)