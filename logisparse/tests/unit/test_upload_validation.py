import pytest
from fastapi import HTTPException, UploadFile

from app.services.upload_validation import detect_content_type, sanitize_filename


def test_detect_content_type_pdf() -> None:
    assert detect_content_type(b"%PDF-1.7 content") == "application/pdf"


def test_detect_content_type_rejects_unknown_bytes() -> None:
    with pytest.raises(HTTPException):
        detect_content_type(b"not a supported file")


def test_sanitize_filename_strips_paths() -> None:
    assert sanitize_filename("../nested/guide.pdf") == "guide.pdf"


def test_upload_file_import_available() -> None:
    assert UploadFile is not None
