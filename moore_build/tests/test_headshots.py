from pathlib import Path
from PIL import Image

from moore_pipeline.headshots import prepare_all_headshots


TME = Path("/Users/jenniferkleiman/Documents/TME")


def test_prepare_all_headshots_produces_three_jpgs(tmp_path):
    out_dir = tmp_path / "assets"
    paths = prepare_all_headshots(
        moore_src=TME / "Moore_Kevin.avif",
        yasuda_src=TME / "Yasuda_Sohei.jpg",
        wong_src=TME / "Wong_Webster.jpg",
        out_dir=out_dir,
        size_px=300,
    )
    assert set(paths.keys()) == {"moore", "yasuda", "wong"}
    for p in paths.values():
        assert p.exists()
        img = Image.open(p)
        assert img.size == (300, 300)
        assert img.format == "JPEG"
