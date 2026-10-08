"""Headshot input handling: EXIF orientation, transparency, mask quality,
cascade load check, grayscale input, face-found return value."""
import cv2
import pytest
from PIL import Image

from tme_template import headshot
from tme_template.headshot import circle_mask, frame_headshot_square, load_headshot


def test_exif_orientation_is_applied_before_cropping(tmp_path):
    # Stored 200x100 landscape: left half red, right half blue, tagged
    # Orientation=6 (rotate 90° clockwise to display). Displayed correctly it
    # is a 100x200 portrait with red on top; the portrait heuristic crop keeps
    # the top, so pixel (90, 10) is red. Without the transpose the crop is the
    # middle of the landscape image and (90, 10) lands in the blue half.
    img = Image.new("RGB", (200, 100), "blue")
    img.paste("red", (0, 0, 100, 100))
    exif = img.getexif()
    exif[0x0112] = 6
    src = tmp_path / "phone.jpg"
    img.save(src, exif=exif)
    out = tmp_path / "out.jpg"

    frame_headshot_square(str(src), str(out), size_px=100, circle=False)

    r, g, b = Image.open(out).getpixel((90, 10))
    assert r > 200 and b < 80


def test_transparent_png_is_flattened_onto_background(tmp_path):
    src = tmp_path / "cutout.png"
    Image.new("RGBA", (120, 120), (0, 0, 0, 0)).save(src)
    out = tmp_path / "out.jpg"

    frame_headshot_square(str(src), str(out), size_px=60, circle=False, bg_rgb=(255, 255, 255))

    r, g, b = Image.open(out).getpixel((30, 30))
    assert min(r, g, b) > 245  # white within JPEG tolerance; used to be 0,0,0


def test_palette_png_with_transparency_is_flattened(tmp_path):
    src = tmp_path / "pal.png"
    Image.new("RGBA", (40, 40), (0, 0, 0, 0)).convert("P").save(src, transparency=0)
    assert load_headshot(src).getpixel((5, 5)) == (255, 255, 255)


def test_grayscale_jpeg_is_handled(tmp_path):
    src = tmp_path / "gray.jpg"
    Image.new("L", (100, 100), 128).save(src)
    out = tmp_path / "out.jpg"
    frame_headshot_square(str(src), str(out), size_px=50)
    assert Image.open(out).mode == "RGB"


def test_circle_mask_is_anti_aliased():
    values = set(circle_mask(64).getdata())
    assert values - {0, 255}, "edge should contain intermediate gray values"


def test_returns_whether_a_face_was_used(tmp_path):
    src = tmp_path / "flat.jpg"
    Image.new("RGB", (100, 140), "gray").save(src)
    assert frame_headshot_square(str(src), str(tmp_path / "o.jpg"), size_px=50) is False


def test_empty_cascade_raises_clearly(monkeypatch):
    class _Empty:
        def empty(self):
            return True

    monkeypatch.setattr(headshot, "_FACE_CASCADE", None)
    monkeypatch.setattr(cv2, "CascadeClassifier", lambda path: _Empty())
    with pytest.raises(RuntimeError, match="cascade"):
        headshot._get_face_cascade()
