from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

PDF_MAGIC = b"%PDF"
JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def sanitize_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required",
        )
    return Path(filename).name.replace("\x00", "").strip()


def detect_content_type(file_bytes: bytes) -> str:
    if file_bytes.startswith(PDF_MAGIC):
        return "application/pdf"
    if file_bytes.startswith(JPEG_MAGIC):
        return "image/jpeg"
    if file_bytes.startswith(PNG_MAGIC):
        return "image/png"
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported or invalid file content",
    )


async def read_and_validate_upload(file: UploadFile) -> tuple[str, str, bytes]:
    filename = sanitize_filename(file.filename)
    extension = Path(filename).suffix.lower().lstrip(".")
    allowed_extensions = {item.lower() for item in settings.ALLOWED_EXTENSIONS}

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension. Allowed: {', '.join(sorted(allowed_extensions))}",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")

    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit",
        )

    content_type = detect_content_type(content)
    extension_content_map = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
    }
    if extension_content_map.get(extension) != content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File extension does not match its content",
        )

    return filename, content_type, content
