import base64
import io
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError


class ImagePreprocessError(ValueError):
    pass


@dataclass(frozen=True)
class PreprocessedImage:
    image: Image.Image
    original_width: int
    original_height: int
    width: int
    height: int
    image_bytes: bytes
    base64_image: str
    numpy_rgb: np.ndarray


def preprocess_image(image_bytes: bytes, max_dimension: int) -> PreprocessedImage:
    try:
        with Image.open(io.BytesIO(image_bytes)) as opened_image:
            original_width, original_height = opened_image.size
            image = ImageOps.exif_transpose(opened_image).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ImagePreprocessError("Invalid image content. Pillow cannot open this file.") from exc

    image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    output_buffer = io.BytesIO()
    image.save(output_buffer, format="JPEG", quality=90)
    processed_bytes = output_buffer.getvalue()

    return PreprocessedImage(
        image=image.copy(),
        original_width=original_width,
        original_height=original_height,
        width=image.width,
        height=image.height,
        image_bytes=processed_bytes,
        base64_image=base64.b64encode(processed_bytes).decode("ascii"),
        numpy_rgb=np.asarray(image, dtype=np.uint8),
    )
