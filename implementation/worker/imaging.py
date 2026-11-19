"""The image work done for every request. Same settings for every request."""

import io

from PIL import Image

OUTPUT_QUALITY = 80


def process_jpeg(data: bytes) -> bytes:
    """Decode a JPEG, resize it to half width and height with LANCZOS, and
    encode it as JPEG quality 80. Odd sizes round down."""
    with Image.open(io.BytesIO(data)) as image:
        half = (image.width // 2, image.height // 2)
        resized = image.resize(half, Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    resized.save(buffer, format="JPEG", quality=OUTPUT_QUALITY)
    return buffer.getvalue()
