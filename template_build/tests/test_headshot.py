import os
from PIL import Image
from tme_template.headshot import (
    frame_headshot_square, _detect_face_center, _face_centered_crop, _heuristic_crop,
)
import cv2
import numpy as np


def test_frame_headshot_produces_square_image(tmp_path):
    # 600x800 test image
    src = tmp_path / "src.jpg"
    Image.new("RGB", (600, 800), color="gray").save(src)
    out = tmp_path / "out.jpg"
    frame_headshot_square(str(src), str(out), size_px=300)
    assert out.exists()
    img = Image.open(out)
    assert img.size == (300, 300)


def test_no_face_falls_back_to_heuristic_crop(tmp_path):
    """Flat gray image (no face) should still produce a valid square output."""
    src = tmp_path / "noface.jpg"
    Image.new("RGB", (600, 800), color="gray").save(src)
    out = tmp_path / "out.jpg"
    frame_headshot_square(str(src), str(out), size_px=300)
    assert out.exists()
    assert Image.open(out).size == (300, 300)


def test_real_headshot_finds_face_and_centers_crop(tmp_path):
    """For a real headshot from the Moore article assets, the function should
    detect a face and produce a square output centered on it (face center
    should be near the middle of the cropped image)."""
    src = "/Users/jenniferkleiman/Documents/TME/Yasuda_Sohei.jpg"
    out = tmp_path / "yasuda_face.jpg"
    frame_headshot_square(src, str(out), size_px=300)
    assert out.exists()
    # Re-detect on the cropped output: face center should be in the middle 60% of the image
    cropped = Image.open(out)
    center = _detect_face_center(cropped)
    assert center is not None, "Face detection failed on cropped Yasuda image"
    cx, cy = center
    assert 60 <= cx <= 240, f"Face X off-center after crop: {cx}"
    assert 60 <= cy <= 240, f"Face Y off-center after crop: {cy}"
