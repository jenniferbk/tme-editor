"""End-to-end pipeline: manuscript + headshots + metadata → starter .docx.
Reuses the existing moore_pipeline.endnote resolver and headshot framing."""
import shutil
from pathlib import Path
from typing import Dict

from PIL import Image

from moore_pipeline.endnote import resolve_endnote_citations
from tme_template.headshot import frame_headshot_square

from article_starter import build_article_starter


def _to_sRGB_jpg(src: Path, dst: Path) -> None:
    Image.open(src).convert("RGB").save(dst, "JPEG", quality=92)


def run_pipeline(
    *,
    manuscript_src: Path,
    headshot_map: Dict[str, Path],  # author name → uploaded image path
    meta,
    work_dir: Path,
) -> Path:
    """Run the full pipeline. Returns path to the final starter .docx."""
    work_dir.mkdir(parents=True, exist_ok=True)

    resolved_docx = work_dir / 'manuscript_resolved.docx'
    resolve_endnote_citations(str(manuscript_src), str(resolved_docx))

    framed: Dict[str, Path] = {}
    assets_dir = work_dir / 'assets'
    assets_dir.mkdir(exist_ok=True)
    for author_name, img_src in headshot_map.items():
        intermediate = assets_dir / f"{author_name.replace(' ', '_')}_intermediate.jpg"
        framed_out = assets_dir / f"{author_name.replace(' ', '_')}_framed.jpg"
        _to_sRGB_jpg(img_src, intermediate)
        frame_headshot_square(str(intermediate), str(framed_out), size_px=300, circle=True)
        intermediate.unlink()
        framed[author_name] = framed_out

    starter_path = work_dir / 'starter.docx'
    build_article_starter(meta=meta, headshots=framed, out_path=starter_path)
    return starter_path
