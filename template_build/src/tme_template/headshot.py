"""Crop-and-resize author headshots to square, centered on the face when detectable."""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


# Lazy-loaded cascade so import-time isn't penalized for callers that don't use detection
_FACE_CASCADE = None


def _get_face_cascade():
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        _FACE_CASCADE = cv2.CascadeClassifier(str(cascade_path))
    return _FACE_CASCADE


def _detect_face_center(pil_img: Image.Image) -> tuple[int, int] | None:
    """Return (cx, cy) of the largest detected face, or None if no face found."""
    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
    cascade = _get_face_cascade()
    faces = cascade.detectMultiScale(cv_img, scaleFactor=1.1, minNeighbors=5,
                                      minSize=(60, 60))
    if len(faces) == 0:
        return None
    # Pick the largest face
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


def frame_headshot_square(src_path: str, out_path: str, size_px: int = 300,
                           circle: bool = True,
                           bg_rgb: tuple[int, int, int] = (255, 255, 255)) -> None:
    """Square-crop a headshot, centered on the face if detectable.

    When circle=True (default), paints everything outside an inscribed circle
    with bg_rgb — yielding a round-looking headshot on that background.
    Saved as JPEG (no alpha); bg_rgb should match the surrounding page color.

    Falls back to a top-biased heuristic crop when no face is found
    (so the function never fails on edge-case images).
    """
    img = Image.open(src_path).convert("RGB")
    w, h = img.size
    face = _detect_face_center(img)
    if face is not None:
        cx, cy = face
        left, top, side = _face_centered_crop(w, h, cx, cy)
    else:
        left, top, side = _heuristic_crop(w, h)
    cropped = img.crop((left, top, left + side, top + side))
    cropped = cropped.resize((size_px, size_px), Image.LANCZOS)
    if circle:
        mask = Image.new("L", (size_px, size_px), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size_px - 1, size_px - 1), fill=255)
        bg = Image.new("RGB", (size_px, size_px), bg_rgb)
        cropped = Image.composite(cropped, bg, mask)
    cropped.save(out_path, "JPEG", quality=90)
