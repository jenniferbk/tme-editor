"""One-shot pipeline: resolve EndNote, prep headshots, generate Moore starter docx.

Outputs:
  - /Users/jenniferkleiman/Documents/TME/moore_build/intermediate/Moore_resolved.docx
  - /Users/jenniferkleiman/Documents/TME/moore_build/assets/{moore,yasuda,wong}_framed.jpg
  - /Users/jenniferkleiman/Documents/TME/TME_Moore_2026_starter.docx
"""
from pathlib import Path

from moore_pipeline.endnote import resolve_endnote_citations
from moore_pipeline.headshots import prepare_all_headshots
from moore_pipeline.moore_starter import build_moore_starter


TME = Path(__file__).resolve().parents[2]
MOORE_SRC = TME / "TME_Moore_2026.docx"
MOORE_AVIF = TME / "Moore_Kevin.avif"
YASUDA_JPG = TME / "Yasuda_Sohei.jpg"
WONG_JPG = TME / "Wong_Webster.jpg"

INTERMEDIATE_DIR = TME / "moore_build" / "intermediate"
ASSETS_DIR = TME / "moore_build" / "assets"
RESOLVED_DOCX = INTERMEDIATE_DIR / "Moore_resolved.docx"
STARTER_DOCX = TME / "TME_Moore_2026_starter.docx"


def run() -> None:
    print(f"1. Resolving EndNote citations in {MOORE_SRC.name} …")
    resolve_endnote_citations(str(MOORE_SRC), str(RESOLVED_DOCX))
    print(f"   → {RESOLVED_DOCX}")

    print("2. Preparing headshots …")
    headshots = prepare_all_headshots(
        moore_src=MOORE_AVIF,
        yasuda_src=YASUDA_JPG,
        wong_src=WONG_JPG,
        out_dir=ASSETS_DIR,
    )
    for name, p in headshots.items():
        print(f"   → {name}: {p}")

    print("3. Building Moore starter document …")
    build_moore_starter(out_path=STARTER_DOCX, headshots=headshots)
    print(f"   → {STARTER_DOCX}")

    print()
    print("Automated pipeline done.")
    print("Open TME_Moore_2026_starter.docx and follow MERGE_INSTRUCTIONS.md.")


if __name__ == "__main__":
    run()
