from typing import Dict, Any, Optional
import logging
from app.services.extractors.base_adapter import BaseAdapter
from app.schemas.extraction import ExtractedLogisticsData

logger = logging.getLogger(__name__)

class GenericLLMAdapter(BaseAdapter):
    
    async def extract_data(
        self,
        text: str,
        image_bytes: bytes | None = None,
        settings: Any = None,
        correction_history: list[dict] | None = None,
    ) -> Dict[str, Any]:
        from openai import AsyncOpenAI
        
        if not settings or not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY no encontrada. Devolviendo JSON mockeado.")
            return {
                "origen": None,
                "destino": None,
                "adapter_used": "GenericLLMAdapter (Fallo API)"
            }

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # Prompt mejorado: instrucciones estrictas y claras
        system_prompt = (
            "Eres un experto en documentos logísticos y tributarios chilenos. "
            "Extrae SOLO los siguientes campos: origen, destino, patente_camion, chofer, fecha_despacho, numero_guia. "
            "SI UN CAMPO NO APARECE EXPLÍCITAMENTE EN EL TEXTO, DEVUELVE null. "
            "NO INVENTES INFORMACIÓN. NO USES FRASES LARGAS. "
            "Para origen y destino, usa nombres de ciudades chilenas (ej: Santiago, Puerto Montt, Concepción). "
            "Para chofer, usa nombre y apellido (ej: Juan Pérez). "
            "Para patente, usa formato XX-XX-12 o XX-1234. "
            "Para número de guía, usa solo números."
        )

        user_content = f"Texto del documento:\n{text[:2000]}"

        # Inyección de correcciones previas (Few-Shot)
        if correction_history:
            examples = "\n".join([
                f"Corrección previa: Campo '{c['field_name']}' fue corregido de '{c['original_value']}' a '{c['corrected_value']}'."
                for c in correction_history[:5]
            ])
            user_content += f"\n\nContexto de correcciones previas:\n{examples}\nTen en cuenta estas correcciones al extraer."

        input_messages: list[Any] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        try:
            response = await client.beta.chat.completions.parse(
                model=settings.OPENAI_MODEL,
                messages=input_messages,
                response_format=ExtractedLogisticsData,
                temperature=0,
            )
            
            parsed_data = response.choices[0].message.parsed
            
            if not parsed_data:
                logger.error("OpenAI falló al estructurar la respuesta (parsed es None).")
                return {"adapter_used": "GenericLLMAdapter (Error de Parseo)"}
            
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