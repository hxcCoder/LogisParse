# app/services/file_manager.py
"""
Gestor de archivos para el sistema de bandeja limpia.
Mueve los documentos procesados a una carpeta de almacenamiento
para mantener la bandeja de entrada ordenada y facilitar auditorías.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── CONFIGURACIÓN ──

DEFAULT_INPUT_DIR = Path("uploads")
DEFAULT_PROCESSED_DIR = Path("procesados")


class FileManager:
    """
    Maneja el ciclo de vida de los archivos:
    - Almacenamiento temporal en /uploads
    - Movimiento a /procesados tras extracción exitosa
    - Organización por fecha para facilitar auditorías
    """

    def __init__(
        self,
        input_dir: str | Path = DEFAULT_INPUT_DIR,
        processed_dir: str | Path = DEFAULT_PROCESSED_DIR,
    ) -> None:
        """
        Inicializa el gestor de archivos.

        Args:
            input_dir: Carpeta donde se reciben los documentos.
            processed_dir: Carpeta donde se mueven tras procesar.
        """
        self.input_dir = Path(input_dir)
        self.processed_dir = Path(processed_dir)

        # Crear carpetas si no existen
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "FileManager inicializado:\n  Entrada: %s\n  Procesados: %s",
            self.input_dir.absolute(),
            self.processed_dir.absolute(),
        )

    def save_uploaded_file(self, file_bytes: bytes, filename: str) -> Path:
        """
        Guarda un archivo subido en la carpeta de entrada.

        Args:
            file_bytes: Bytes del archivo.
            filename: Nombre original del archivo.

        Returns:
            Ruta completa del archivo guardado.

        Raises:
            IOError: Si no se puede escribir el archivo.
        """
        safe_filename = self._sanitize_filename(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{safe_filename}"

        filepath = self.input_dir / unique_filename

        try:
            filepath.write_bytes(file_bytes)
            logger.info("Archivo guardado en entrada: %s", filepath)
            return filepath
        except IOError as exc:
            logger.exception("Error al guardar archivo en entrada")
            raise IOError(f"No se pudo guardar {filename}: {str(exc)}") from exc

    def move_to_processed(
        self, filepath: str | Path, subfolder: str | None = None
    ) -> Path:
        """
        Mueve un archivo procesado a la carpeta /procesados.
        Preserva el archivo original para auditoría.

        Args:
            filepath: Ruta del archivo a mover.
            subfolder: Subcarpeta opcional (ej: nombre del adaptador o fecha).

        Returns:
            Nueva ruta del archivo en /procesados.

        Raises:
            FileNotFoundError: Si el archivo original no existe.
            IOError: Si no se puede mover el archivo.
        """
        source = Path(filepath)

        if not source.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {source}")

        # Construir destino
        dest_dir = self.processed_dir
        if subfolder:
            dest_dir = dest_dir / subfolder
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Si ya existe, añadir sufijo para evitar colisiones
        dest = dest_dir / source.name
        if dest.exists():
            stem = dest.stem
            suffix = dest.suffix
            counter = 1
            while dest.exists():
                dest = dest_dir / f"{stem}_{counter}{suffix}"
                counter += 1

        try:
            shutil.move(str(source), str(dest))
            logger.info(
                "Archivo movido a procesados: %s → %s", source.name, dest
            )
            return dest
        except (IOError, OSError) as exc:
            logger.exception("Error al mover archivo a procesados")
            raise IOError(
                f"No se pudo mover {source.name} a procesados: {str(exc)}"
            ) from exc

    def get_input_files(self, extension: str | None = None) -> list[Path]:
        """
        Lista los archivos pendientes en la carpeta de entrada.

        Args:
            extension: Filtrar por extensión (ej: '.pdf').

        Returns:
            Lista de rutas de archivos en la bandeja de entrada.
        """
        if extension:
            return list(self.input_dir.glob(f"*{extension}"))
        return [f for f in self.input_dir.iterdir() if f.is_file()]

    def get_processed_files(
        self, days: int | None = None
    ) -> list[Path]:
        """
        Lista archivos procesados para auditoría.

        Args:
            days: Solo mostrar archivos de los últimos N días.

        Returns:
            Lista de rutas de archivos procesados.
        """
        files = [f for f in self.processed_dir.rglob("*") if f.is_file()]

        if days is not None:
            cutoff = datetime.now().timestamp() - (days * 86400)
            files = [f for f in files if f.stat().st_mtime > cutoff]

        return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)

    # ── MÉTODOS PRIVADOS ──

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        Limpia un nombre de archivo para evitar inyección de rutas.

        Args:
            filename: Nombre original del archivo.

        Returns:
            Nombre seguro (sin caracteres de ruta).
        """
        # Eliminar caracteres peligrosos y rutas
        safe = Path(filename).name
        # Reemplazar espacios y caracteres especiales
        safe = "".join(c for c in safe if c.isalnum() or c in "._- ")
        safe = safe.strip().replace(" ", "_")
        return safe or "unnamed_file"


# ── FACTORY ──

def create_file_manager(
    input_dir: str | Path = DEFAULT_INPUT_DIR,
    processed_dir: str | Path = DEFAULT_PROCESSED_DIR,
) -> FileManager:
    """
    Crea una instancia de FileManager con las rutas especificadas.

    Args:
        input_dir: Carpeta de entrada.
        processed_dir: Carpeta de procesados.

    Returns:
        Instancia de FileManager.
    """
    return FileManager(input_dir=input_dir, processed_dir=processed_dir)