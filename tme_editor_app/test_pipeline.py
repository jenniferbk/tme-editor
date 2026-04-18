"""Offline smoke test: run the app's pipeline end-to-end with Moore as input,
without invoking Streamlit or Gemini. Constructs ArticleMeta directly.
"""
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
TME = HERE.parent
for p in (HERE / 'src', TME / 'template_build' / 'src', TME / 'moore_build' / 'src'):
    sys.path.insert(0, str(p))

from extractor import ArticleMeta, AuthorMeta
from pipeline import run_pipeline
from apply_styles import apply_styles
from fixup import run_fixup


MOORE_META = ArticleMeta(
    title=(
        "Integration by Substitution: An Emergent Quantitative Reasoning "
        "Approach to U-Substitution"
    ),
    authors=[
        AuthorMeta(
            name="Kevin C. Moore", affiliation_num=1, corresponding=True,
            email="kvcmoore@uga.edu",
            bio=(
                "Kevin C. Moore is a Professor of Mathematics Education at University "
                "of Georgia. His primary research focuses on quantitative reasoning."
            ),
        ),
        AuthorMeta(
            name="Sohei Yasuda", affiliation_num=1,
            bio="Sohei Yasuda is a graduate student at the University of Georgia.",
        ),
        AuthorMeta(
            name="Webster Wong", affiliation_num=1,
            bio="Webster Wong is a graduate student at the University of Georgia.",
        ),
    ],
    affiliations=["Department of Mathematics and Science Education, University of Georgia"],
    abstract=(
        "In this paper, we present a conceptual analysis for integration by "
        "substitution that centers major ideas of quantitative reasoning."
    ),
    keywords=["Conceptual Analysis", "Integration by Substitution", "Quantitative Reasoning"],
    received="Dec 3, 2024", revised="Jan 22, 2025",
    accepted="Apr 3, 2025", published="Apr 2026",
    doi="doi.org/10.xxxxx/tme.2026.34.1.01",
    volume=34, number=1, year=2026, pages="1–24",
)


def main() -> None:
    work_dir = Path(tempfile.mkdtemp(prefix="tme_app_test_"))
    print(f"work_dir = {work_dir}")

    # Phase 1: build cover
    manuscript = TME / "TME_Moore_2026.docx"
    headshots = {
        "Kevin C. Moore":  TME / "Moore_Kevin.avif",
        "Sohei Yasuda":    TME / "Yasuda_Sohei.jpg",
        "Webster Wong":    TME / "Wong_Webster.jpg",
    }
    print("\n=== Phase 1: run_pipeline ===")
    starter = run_pipeline(
        manuscript_src=manuscript,
        headshot_map=headshots,
        meta=MOORE_META,
        work_dir=work_dir,
    )
    print(f"  starter.docx written: {starter} ({starter.stat().st_size} bytes)")

    # Save to a stable location so we can open it in Word and compare
    final_starter = TME / "tme_editor_app" / "_test_output_starter.docx"
    shutil.copy2(starter, final_starter)
    print(f"  copied to {final_starter}")

    # Phase 2: simulate editor returning with a populated docx.
    # For smoke-test, we use the existing pre-fixup Moore starter — it was
    # populated via Word paste already.
    print("\n=== Phase 2: apply_styles + fixup on pre-fixup Moore starter ===")
    simulated_populated = TME / "TME_Moore_2026_starter.pre-fixup.docx"
    proof_path = work_dir / "proof.docx"
    shutil.copy2(simulated_populated, proof_path)

    style_stats = apply_styles(str(proof_path), MOORE_META)
    print(f"  apply_styles stats: {style_stats}")

    fixup_stats = run_fixup(str(proof_path))
    print(f"  fixup stats: {fixup_stats}")

    final_proof = TME / "tme_editor_app" / "_test_output_proof.docx"
    shutil.copy2(proof_path, final_proof)
    print(f"  copied to {final_proof}")

    print("\nDone. Open the two _test_output_* files in Word to compare.")


if __name__ == "__main__":
    main()
