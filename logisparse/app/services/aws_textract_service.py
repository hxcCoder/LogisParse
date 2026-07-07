# app/services/aws_textract_service.py
"""
Servicio de integración con AWS Textract para extracción de texto,
tablas y formularios de documentos escaneados.

Dependencias:
    pip install boto3

Configuración en .env:
    AWS_ACCESS_KEY_ID=tu_access_key
    AWS_SECRET_ACCESS_KEY=tu_secret_key
    AWS_REGION=us-east-1
    AWS_TEXTRACT_BUCKET=logisparse-documents  (opcional, para async)
"""

import logging
import time
from io import BytesIO
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


class AWSTextractService:
    """
    Cliente wrapper para AWS Textract.
    Soporta extracción síncrona (imágenes) y asíncrona (PDFs multipágina).
    """

    def __init__(self, region_name: str = "us-east-1") -> None:
        """
        Inicializa el cliente de Textract.

        Args:
            region_name: Región de AWS donde está habilitado Textract.
        """
        self.region_name = region_name
        self.client = boto3.client(
            "textract",
            region_name=region_name,
        )

    # ── MÉTODOS SÍNCRONOS (IMÁGENES, PDFs DE UNA PÁGINA) ──

    def extract_text(self, file_bytes: bytes) -> str:
        """
        Extrae texto plano del documento usando DetectDocumentText.

        Args:
            file_bytes: Bytes del archivo (JPEG, PNG o PDF de una página).

        Returns:
            Texto extraído concatenado.

        Raises:
            ValueError: Si el archivo está vacío.
            RuntimeError: Si AWS Textract falla.
        """
        if not file_bytes:
            raise ValueError("El archivo está vacío. No se puede enviar a Textract.")

        try:
            logger.info(
                "Enviando documento a AWS Textract (DetectDocumentText)..."
            )
            response = self.client.detect_document_text(
                Document={"Bytes": file_bytes}
            )

            blocks = response.get("Blocks", [])
            text_lines: list[str] = []

            for block in blocks:
                if block.get("BlockType") == "LINE":
                    text = block.get("Text", "")
                    if text.strip():
                        text_lines.append(text)

            extracted_text = "\n".join(text_lines)
            logger.info(
                "Textract extrajo %d líneas de texto.", len(text_lines)
            )
            return extracted_text

        except (BotoCoreError, ClientError) as exc:
            logger.exception("Error en AWS Textract (DetectDocumentText)")
            raise RuntimeError(
                f"AWS Textract falló al extraer texto: {str(exc)}"
            ) from exc

    def extract_tables_and_forms(self, file_bytes: bytes) -> dict[str, Any]:
        """
        Extrae tablas y formularios usando AnalyzeDocument.

        Args:
            file_bytes: Bytes del archivo.

        Returns:
            Diccionario con:
                - tables: Lista de tablas extraídas (celdas, filas, columnas)
                - forms: Lista de pares clave-valor de formularios
                - raw_blocks: Bloques completos de la respuesta
        """
        if not file_bytes:
            raise ValueError("El archivo está vacío.")

        try:
            logger.info(
                "Enviando documento a AWS Textract (AnalyzeDocument - TABLES | FORMS)..."
            )
            response = self.client.analyze_document(
                Document={"Bytes": file_bytes},
                FeatureTypes=["TABLES", "FORMS"],
            )

            blocks = response.get("Blocks", [])
            tables = self._parse_tables(blocks)
            forms = self._parse_forms(blocks)

            logger.info(
                "Textract extrajo %d tablas y %d campos de formulario.",
                len(tables),
                len(forms),
            )

            return {
                "tables": tables,
                "forms": forms,
                "raw_blocks": blocks,
            }

        except (BotoCoreError, ClientError) as exc:
            logger.exception("Error en AWS Textract (AnalyzeDocument)")
            raise RuntimeError(
                f"AWS Textract falló al analizar tablas/formularios: {str(exc)}"
            ) from exc

    # ── MÉTODOS ASÍNCRONOS (PDFs MULTIPÁGINA) ──

    def start_document_analysis(
        self, file_bytes: bytes, s3_bucket: str, s3_key: str
    ) -> str:
        """
        Inicia análisis asíncrono para documentos grandes (PDF multipágina).

        Args:
            file_bytes: Bytes del documento.
            s3_bucket: Nombre del bucket S3 donde está almacenado.
            s3_key: Clave del objeto en S3.

        Returns:
            JobId del trabajo de Textract.
        """
        try:
            # Subir a S3 primero (requiere implementación aparte o usar bytes directamente)
            # Para simplificar, usamos bytes si el PDF es pequeño, o S3 para grandes.
            response = self.client.start_document_analysis(
                DocumentLocation={
                    "S3Object": {
                        "Bucket": s3_bucket,
                        "Name": s3_key,
                    }
                },
                FeatureTypes=["TABLES", "FORMS"],
            )
            job_id = response["JobId"]
            logger.info("Trabajo asíncrono iniciado con JobId: %s", job_id)
            return job_id

        except (BotoCoreError, ClientError) as exc:
            logger.exception("Error al iniciar análisis asíncrono")
            raise RuntimeError(
                f"No se pudo iniciar el análisis asíncrono: {str(exc)}"
            ) from exc

    def get_document_analysis(self, job_id: str) -> dict[str, Any]:
        """
        Obtiene los resultados de un trabajo asíncrono.

        Args:
            job_id: ID del trabajo devuelto por start_document_analysis.

        Returns:
            Diccionario con tablas, formularios y bloques extraídos.
        """
        try:
            max_retries = 30
            delay = 2  # segundos entre polling

            for attempt in range(max_retries):
                response = self.client.get_document_analysis(JobId=job_id)
                status = response["JobStatus"]

                if status == "SUCCEEDED":
                    blocks = response.get("Blocks", [])
                    return {
                        "tables": self._parse_tables(blocks),
                        "forms": self._parse_forms(blocks),
                        "raw_blocks": blocks,
                    }
                elif status == "FAILED":
                    raise RuntimeError(
                        f"Textract Job {job_id} falló: {response.get('StatusMessage')}"
                    )

                logger.debug(
                    "Esperando Job %s... (intento %d/%d)",
                    job_id,
                    attempt + 1,
                    max_retries,
                )
                time.sleep(delay)

            raise TimeoutError(
                f"Tiempo de espera agotado para Job {job_id}"
            )

        except (BotoCoreError, ClientError) as exc:
            logger.exception("Error obteniendo resultados asíncronos")
            raise RuntimeError(
                f"Error al obtener resultados del Job {job_id}: {str(exc)}"
            ) from exc

    # ── PARSERS INTERNOS ──

    def _parse_tables(self, blocks: list[dict]) -> list[dict]:
        """
        Convierte los bloques de tabla de Textract en una estructura
        más usable (lista de filas con celdas).

        Args:
            blocks: Lista de bloques de la respuesta de Textract.

        Returns:
            Lista de tablas, cada una con filas y celdas.
        """
        block_map = {b["Id"]: b for b in blocks}
        tables: list[dict] = []

        for block in blocks:
            if block.get("BlockType") != "TABLE":
                continue

            table_data: dict[str, Any] = {
                "id": block["Id"],
                "confidence": block.get("Confidence", 0),
                "rows": [],
            }

            # Buscar relaciones hijo (CELLs dentro de esta TABLE)
            relationships = block.get("Relationships", [])
            for rel in relationships:
                if rel.get("Type") != "CHILD":
                    continue

                cell_ids = rel.get("Ids", [])
                # Agrupar celdas por fila (RowIndex)
                rows_dict: dict[int, list[str]] = {}

                for cell_id in cell_ids:
                    cell = block_map.get(cell_id, {})
                    if cell.get("BlockType") == "CELL":
                        row_idx = cell.get("RowIndex", 1)
                        text = cell.get("Text", "").strip()
                        if row_idx not in rows_dict:
                            rows_dict[row_idx] = []
                        rows_dict[row_idx].append(text)

                # Ordenar filas por índice
                sorted_rows = [
                    rows_dict[idx]
                    for idx in sorted(rows_dict.keys())
                ]
                table_data["rows"] = sorted_rows

            tables.append(table_data)

        return tables

    def _parse_forms(self, blocks: list[dict]) -> dict[str, str]:
        """
        Extrae pares clave-valor de formularios (campos de factura).

        Args:
            blocks: Lista de bloques de la respuesta de Textract.

        Returns:
            Diccionario con clave (label) → valor (value).
        """
        block_map = {b["Id"]: b for b in blocks}
        key_map: dict[str, str] = {}
        value_map: dict[str, str] = {}

        # Primero, identificar KEYS y VALUES
        for block in blocks:
            block_type = block.get("BlockType")
            if block_type == "KEY_VALUE_SET":
                entity_types = block.get("EntityTypes", [])
                if "KEY" in entity_types:
                    # Extraer texto del KEY desde sus hijos
                    text = self._get_child_text(block, block_map)
                    key_map[block["Id"]] = text
                elif "VALUE" in entity_types:
                    text = self._get_child_text(block, block_map)
                    value_map[block["Id"]] = text

        # Luego, relacionar KEYs con VALUEs
        form_data: dict[str, str] = {}
        for block in blocks:
            if block.get("BlockType") != "KEY_VALUE_SET":
                continue
            if "KEY" not in block.get("EntityTypes", []):
                continue

            key_text = key_map.get(block["Id"], "")
            relationships = block.get("Relationships", [])
            for rel in relationships:
                if rel.get("Type") == "VALUE":
                    for value_id in rel.get("Ids", []):
                        value_text = value_map.get(value_id, "")
                        if key_text:
                            form_data[key_text] = value_text

        return form_data

    def _get_child_text(
        self, block: dict, block_map: dict
    ) -> str:
        """
        Obtiene el texto concatenado de los bloques hijos (WORDs).

        Args:
            block: Bloque padre (KEY_VALUE_SET).
            block_map: Mapa de todos los bloques por ID.

        Returns:
            Texto concatenado de los hijos.
        """
        texts: list[str] = []
        for rel in block.get("Relationships", []):
            if rel.get("Type") == "CHILD":
                for child_id in rel.get("Ids", []):
                    child = block_map.get(child_id, {})
                    if child.get("BlockType") == "WORD":
                        word = child.get("Text", "")
                        if word.strip():
                            texts.append(word)
        return " ".join(texts)


# ── FACTORY FUNCTION ──

def create_textract_service(region_name: str = "us-east-1") -> AWSTextractService:
    """
    Crea una instancia del servicio AWS Textract.

    Args:
        region_name: Región de AWS (por defecto us-east-1).

    Returns:
        Instancia de AWSTextractService lista para usar.
    """
    return AWSTextractService(region_name=region_name)