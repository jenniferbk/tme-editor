"""Image normalization for python-docx picture insertion."""
import io

from PIL import Image


def open_image_as_rgb_stream(path: str) -> io.BytesIO:
    """Open an image and return it as an in-memory sRGB JPEG stream.

    python-docx cannot embed CMYK JPEGs or palette PNGs with transparency
    reliably, so every logo goes through this. Raises FileNotFoundError for a
    missing file and PIL.UnidentifiedImageError for a non-image; library code
    does not swallow those — the caller decides what a missing logo means.
    """
    with Image.open(path) as img:
        rgb = img.convert("RGB")
    buf = io.BytesIO()
    rgb.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    return buf
