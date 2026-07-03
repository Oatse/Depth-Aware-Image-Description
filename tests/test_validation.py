import io
import asyncio

from fastapi import UploadFile
from PIL import Image
import pytest

from services.image_preprocess import preprocess_image
from services.validation import ImageValidationError, validate_upload_file


def _image_bytes(format_name: str = "JPEG") -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 20), color=(120, 140, 160)).save(buffer, format=format_name)
    return buffer.getvalue()


def test_validate_upload_file_accepts_valid_image() -> None:
    file = UploadFile(filename="sample.jpg", file=io.BytesIO(_image_bytes()), headers={"content-type": "image/jpeg"})

    validated = asyncio.run(validate_upload_file(file, max_size_mb=1))

    assert validated.filename == "sample.jpg"
    assert validated.content_type == "image/jpeg"
    assert validated.size_bytes > 0


def test_validate_upload_file_rejects_empty_file() -> None:
    file = UploadFile(filename="empty.jpg", file=io.BytesIO(b""), headers={"content-type": "image/jpeg"})

    with pytest.raises(ImageValidationError, match="empty"):
        asyncio.run(validate_upload_file(file, max_size_mb=1))


def test_validate_upload_file_rejects_invalid_content_type() -> None:
    file = UploadFile(filename="notes.txt", file=io.BytesIO(b"hello"), headers={"content-type": "text/plain"})

    with pytest.raises(ImageValidationError, match="Invalid image"):
        asyncio.run(validate_upload_file(file, max_size_mb=1))


def test_preprocess_image_converts_to_rgb_and_resizes() -> None:
    processed = preprocess_image(_image_bytes("PNG"), max_dimension=16)

    assert processed.image.mode == "RGB"
    assert max(processed.width, processed.height) <= 16
    assert processed.numpy_rgb.shape[2] == 3
    assert processed.base64_image
