"""Headshot preparation for the Moore article cover page."""
from pathlib import Path
from typing import Dict

from PIL import Image

from tme_template.headshot import frame_headshot_square


def _convert_to_rgb_jpg(src: Path, dst: Path) -> None:
    """Open any format Pillow supports (including AVIF if pillow-avif-plugin installed,
    else pillow 10.4+ native), re-save as standard sRGB JPEG."""
    img = Image.open(src).convert("RGB")
    img.save(dst, "JPEG", quality=92)


def prepare_all_headshots(
    *, moore_src: Path, yasuda_src: Path, wong_src: Path,
    out_dir: Path, size_px: int = 300,
) -> Dict[str, Path]:
    """Convert (if needed) and frame each headshot. Returns a dict of
    {'moore': path, 'yasuda': path, 'wong': path}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    # Intermediate JPGs (normalized to sRGB JPEG regardless of source format)
    intermediates = {}
    for name, src in [("moore", moore_src), ("yasuda", yasuda_src), ("wong", wong_src)]:
        intermediate = out_dir / f"{name}_intermediate.jpg"
        _convert_to_rgb_jpg(src, intermediate)
        intermediates[name] = intermediate

    # Framed outputs
    framed = {}
    for name, intermediate in intermediates.items():
        out = out_dir / f"{name}_framed.jpg"
        frame_headshot_square(str(intermediate), str(out), size_px=size_px)
        framed[name] = out
        # Clean up intermediate
        intermediate.unlink()

    return framed
