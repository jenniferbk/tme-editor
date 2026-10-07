"""Regression guard for headshot cropping's OpenCV dependency.

OpenCV 5.0 moved CascadeClassifier (Haar face detection) out of the core
objdetect module into the contrib-only xobjdetect module and stopped shipping
the Haar XML files. headshot.py relies on both, so opencv-python-headless must
stay on the 4.x line (pinned ``<5`` in requirements.txt and pyproject.toml).
These tests fail loudly if a future environment resolves to OpenCV 5.
"""
from pathlib import Path

import cv2
from PIL import Image

from tme_template.headshot import frame_headshot_square


def test_opencv_provides_haar_cascade_classifier():
    assert hasattr(cv2, "CascadeClassifier"), (
        f"opencv {cv2.__version__} has no CascadeClassifier; "
        "opencv-python-headless must be pinned <5"
    )
    xml = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    assert xml.exists(), f"Haar cascade XML missing from {cv2.data.haarcascades}"


def test_frame_headshot_square_runs_end_to_end(tmp_path):
    src = tmp_path / "in.jpg"
    out = tmp_path / "out.jpg"
    Image.new("RGB", (400, 600), (120, 90, 70)).save(src)

    frame_headshot_square(str(src), str(out), size_px=300, circle=True)

    with Image.open(out) as result:
        assert result.size == (300, 300)
        assert result.mode == "RGB"
