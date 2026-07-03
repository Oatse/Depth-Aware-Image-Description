from dataclasses import dataclass

from fastapi import UploadFile


ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


@dataclass(frozen=True)
class ValidatedUpload:
    filename: str
    content_type: str
    data: bytes
    size_bytes: int


class ImageValidationError(ValueError):
    pass


async def validate_upload_file(file: UploadFile | None, max_size_mb: int) -> ValidatedUpload:
    if file is None:
        raise ImageValidationError("Image file is required.")

    filename = file.filename or "uploaded_image"
    content_type = file.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ImageValidationError("Invalid image file. Please upload JPG, PNG, or WEBP.")

    data = await file.read()
    size_bytes = len(data)
    if size_bytes == 0:
        raise ImageValidationError("Image file is empty.")

    max_size_bytes = max_size_mb * 1024 * 1024
    if size_bytes > max_size_bytes:
        raise ImageValidationError(f"Image file is too large. Maximum size is {max_size_mb} MB.")

    return ValidatedUpload(
        filename=filename,
        content_type=content_type,
        data=data,
        size_bytes=size_bytes,
    )
