from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from app.services.upload_validation import (
    detect_content_type,
    read_and_validate_upload,
    sanitize_filename,
)


def test_detect_content_type_pdf() -> None:
    assert detect_content_type(b"%PDF-1.7 content") == "application/pdf"


def test_detect_content_type_png() -> None:
    assert detect_content_type(b"\x89PNG\r\n\x1a\ncontent") == "image/png"


def test_detect_content_type_jpeg() -> None:
    assert detect_content_type(b"\xff\xd8\xff\xe0content") == "image/jpeg"


def test_detect_content_type_rejects_unknown_bytes() -> None:
    with pytest.raises(HTTPException):
        detect_content_type(b"not a supported file")


def test_sanitize_filename_strips_paths() -> None:
    assert sanitize_filename("../nested/guide.pdf") == "guide.pdf"


def test_sanitize_filename_rejects_missing_name() -> None:
    with pytest.raises(HTTPException):
        sanitize_filename(None)


@pytest.mark.asyncio
async def test_read_and_validate_upload_rejects_empty_file() -> None:
    upload = UploadFile(filename="empty.pdf", file=BytesIO(b""))

    with pytest.raises(HTTPException):
        await read_and_validate_upload(upload)


@pytest.mark.asyncio
async def test_read_and_validate_upload_accepts_pdf() -> None:
    upload = UploadFile(filename="guide.pdf", file=BytesIO(b"%PDF-1.7 content"))

    filename, content_type, content = await read_and_validate_upload(upload)

    assert filename == "guide.pdf"
    assert content_type == "application/pdf"
    assert content.startswith(b"%PDF")


def test_upload_file_import_available() -> None:
    assert UploadFile is not None
