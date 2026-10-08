"""Crop-and-resize author headshots to square, centered on the face when detectable."""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps


# Lazy-loaded cascade so import-time isn't penalized for callers that don't use detection
_FACE_CASCADE = None


def _get_face_cascade():
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        cascade = cv2.CascadeClassifier(str(cascade_path))
        if cascade.empty():
            raise RuntimeError(
                f"OpenCV face cascade failed to load from {cascade_path}; "
                "check the opencv-python-headless install (must be <5)."
            )
        _FACE_CASCADE = cascade
    return _FACE_CASCADE


def _detect_face_center(pil_img: Image.Image) -> tuple[int, int] | None:
    """Return (cx, cy) of the largest detected face, or None if no face found."""
    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
    # Scale the minimum face size with the image so small source photos can
    # still match; a fixed 60px floor never fires on a 200px thumbnail.
    min_side = max(24, min(pil_img.size) // 8)
    faces = _get_face_cascade().detectMultiScale(
        cv_img, scaleFactor=1.1, minNeighbors=5, minSize=(min_side, min_side))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return (x + w // 2, y + h // 2)


def _heuristic_crop(w: int, h: int) -> tuple[int, int, int]:
    """Fallback when no face is detected: top-bias for portraits, center for landscape."""
    side = min(w, h)
    left = (w - side) // 2
    if h > w:
        top = max(0, (h // 3) - (side // 2))
        top = min(top, h - side)
    else:
        top = (h - side) // 2
    return left, top, side


def _face_centered_crop(w: int, h: int, cx: int, cy: int) -> tuple[int, int, int]:
    """Square crop centered on (cx, cy), clamped to image bounds."""
    side = min(w, h)
    half = side // 2
    left = max(0, min(cx - half, w - side))
    top = max(0, min(cy - half, h - side))
    return left, top, side


def load_headshot(src_path, bg_rgb: tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    """Open an image the way a viewer shows it: EXIF orientation applied and
    any transparency flattened onto bg_rgb. Always returns an RGB image."""
    with Image.open(src_path) as raw:
        img = ImageOps.exif_transpose(raw)
        img.load()
    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
    if has_alpha:
        rgba = img.convert("RGBA")
        flat = Image.new("RGB", rgba.size, bg_rgb)
        flat.paste(rgba, mask=rgba.getchannel("A"))
        return flat
    return img.convert("RGB")


def circle_mask(size_px: int, supersample: int = 4) -> Image.Image:
    """Anti-aliased circular mask: drawn at supersample× and downsampled, so
    the circle edge is smooth instead of stepping from 255 to 0."""
    big = size_px * supersample
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, big - 1, big - 1), fill=255)
    return mask.resize((size_px, size_px), Image.Resampling.LANCZOS)


def frame_headshot_square(src_path: str, out_path: str, size_px: int = 300,
                          circle: bool = True,
                          bg_rgb: tuple[int, int, int] = (255, 255, 255)) -> bool:
    """Square-crop a headshot, centered on the face if detectable.

    When circle=True (default), paints everything outside an inscribed circle
    with bg_rgb — yielding a round-looking headshot on that background.
    Saved as JPEG (no alpha); bg_rgb should match the surrounding page color.

    Returns True when a face was detected and used for the crop, False when
    the top-biased heuristic crop was used, so callers can flag photos that
    deserve a manual look.
    """
    img = load_headshot(src_path, bg_rgb)
    w, h = img.size
    face = _detect_face_center(img)
    if face is not None:
        left, top, side = _face_centered_crop(w, h, *face)
    else:
        left, top, side = _heuristic_crop(w, h)
    cropped = img.crop((left, top, left + side, top + side))
    cropped = cropped.resize((size_px, size_px), Image.Resampling.LANCZOS)
    if circle:
        bg = Image.new("RGB", (size_px, size_px), bg_rgb)
        cropped = Image.composite(cropped, bg, circle_mask(size_px))
    cropped.save(out_path, "JPEG", quality=90)
    return face is not None
