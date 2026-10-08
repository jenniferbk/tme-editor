"""End-to-end pipeline: manuscript + headshots + metadata → starter .docx."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from endnote import resolve_endnote_citations
from tme_template.headshot import frame_headshot_square

from article_starter import build_article_starter
from session_meta import embed_meta


@dataclass
class PipelineResult:
    starter_path: Path
    no_face_authors: List[str] = field(default_factory=list)  # headshots that used the fallback crop


def run_pipeline(*, manuscript_src: Path, headshot_map: Dict[str, Path], meta, work_dir: Path) -> PipelineResult:
    """Run the full pipeline. The starter carries `meta` in a Word document
    variable so Phase 2 can recover it without the browser session."""
    work_dir.mkdir(parents=True, exist_ok=True)

    resolved_docx = work_dir / 'manuscript_resolved.docx'
    resolve_endnote_citations(str(manuscript_src), str(resolved_docx))

    framed: Dict[str, Path] = {}
    no_face: List[str] = []
    assets_dir = work_dir / 'assets'
    assets_dir.mkdir(exist_ok=True)
    for author_name, img_src in headshot_map.items():
        framed_out = assets_dir / f"{author_name.replace(' ', '_')}_framed.jpg"
        # frame_headshot_square opens any Pillow-readable file itself; the
        # old intermediate JPEG only added a second round of compression.
        found = frame_headshot_square(str(img_src), str(framed_out), size_px=300, circle=True)
        if not found:
            no_face.append(author_name)
        framed[author_name] = framed_out

    starter_path = work_dir / 'starter.docx'
    build_article_starter(meta=meta, headshots=framed, out_path=starter_path)
    embed_meta(starter_path, meta)
    return PipelineResult(starter_path=starter_path, no_face_authors=no_face)
