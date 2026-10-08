"""Streamlit UI for the TME editor app.

Flow:
  Phase 1 — Cover build
    1. Editor uploads manuscript.docx
    2. App extracts text and calls Gemini Flash for structured metadata
    3. Editor reviews / corrects the extracted fields
    4. Editor uploads headshot files and matches each to an author
    5. Click Build → pipeline runs → download starter.docx (carries the metadata)

  [Manual Word step — see instructions in Phase 2]

  Phase 2 — Finalize proof (works in a fresh session: metadata is read back
  from the uploaded starter)
    6. Editor opens starter in Word, pastes body (Keep Source Formatting), saves
    7. Editor uploads the populated docx
    8. Click Finalize → apply_styles + fixup run → download proof.docx
"""
import shutil
import sys
import tempfile
from pathlib import Path

import streamlit as st
from PIL import features as pil_features

_HERE = Path(__file__).parent
_TME = _HERE.parent
for p in (_HERE / 'src', _TME / 'template_build' / 'src'):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

from apply_styles import apply_styles
from extractor import ArticleMeta, extract_manuscript_text, extract_metadata
from fixup import run_fixup, swap_captions_above
from pipeline import run_pipeline
from session_meta import choose_meta, read_meta

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
# AVIF needs a Pillow built with libavif; offer it only when this install has it.
HEADSHOT_TYPES = ['jpg', 'jpeg', 'png', 'webp'] + (['avif'] if pil_features.check('avif') else [])

st.set_page_config(page_title="TME Editor", page_icon="📝", layout="wide")
st.title("The Mathematics Educator — Article Builder")
st.caption(
    "Upload a submitted manuscript and headshots. The app extracts metadata "
    "with Gemini, lets you review it, then builds a formatted starter .docx. "
    "After pasting the body in Word, come back to finalize into a proof."
)

# --- Session state ---
_DEFAULTS = {
    "meta": None,
    "manuscript_path": None,
    "manuscript_sig": None,     # file_id of the upload we saved
    "starter_bytes": None,
    "proof_bytes": None,
    "proof_filename": None,
}
for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default
if "work_dir" not in st.session_state:
    st.session_state.work_dir = Path(tempfile.mkdtemp(prefix="tme_editor_"))


st.session_state.setdefault("uploader_epoch", 0)


def _reset_session():
    epoch = st.session_state.get("uploader_epoch", 0)
    work_dir = st.session_state.work_dir
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    # Uploader widgets keep their files in browser state; a new key makes
    # Streamlit build fresh, empty uploaders.
    st.session_state["uploader_epoch"] = epoch + 1
    shutil.rmtree(work_dir, ignore_errors=True)
    st.rerun()


def _save_upload(uploaded, subdir: str, name: str) -> Path:
    folder = st.session_state.work_dir / subdir
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_bytes(uploaded.getvalue())
    return path


def _output_filename(meta, kind: str) -> str:
    last = "Author"
    if meta.authors and meta.authors[0].name:
        last = meta.authors[0].name.rsplit(" ", 1)[-1]
    last = "".join(c for c in last if c.isalnum() or c in "-_")
    return f"TME_{last}_{meta.year}_{kind}.docx"


with st.sidebar:
    if st.button("Start over (clear everything)"):
        _reset_session()

# =========================================================================
# Phase 1 — Cover build
# =========================================================================

st.header("Phase 1 — Cover build")

st.subheader("1. Upload manuscript")
ms = st.file_uploader("Submitted manuscript (.docx)", type=['docx'], key=f"ms_upload_{st.session_state.uploader_epoch}")
if ms is not None:
    sig = ms.file_id
    if sig != st.session_state.manuscript_sig:
        st.session_state.manuscript_path = _save_upload(ms, "manuscript", "manuscript.docx")
        st.session_state.manuscript_sig = sig
        st.session_state.meta = None          # new manuscript → re-extract
        st.session_state.starter_bytes = None

if st.session_state.manuscript_path and st.session_state.meta is None:
    if st.button("Extract metadata with Gemini"):
        with st.spinner("Reading manuscript and calling Gemini Flash…"):
            text = extract_manuscript_text(str(st.session_state.manuscript_path))
            try:
                st.session_state.meta = extract_metadata(text)
                st.success("Extracted. Review below.")
            except Exception as e:
                st.error(f"Extraction failed: {e}")

if st.session_state.meta is not None:
    meta: ArticleMeta = st.session_state.meta

    st.subheader("2. Review & correct")
    col1, col2 = st.columns(2)
    with col1:
        meta.title = st.text_area("Title", meta.title, height=80, key="m_title")
        meta.abstract = st.text_area("Abstract", meta.abstract, height=200, key="m_abstract")
        meta.keywords = [k.strip() for k in st.text_input(
            "Keywords (comma-separated)", ", ".join(meta.keywords), key="m_keywords"
        ).split(",") if k.strip()]
    with col2:
        meta.volume = int(st.number_input("Volume", value=int(meta.volume), step=1, key="m_volume"))
        meta.number = int(st.number_input("Number", value=int(meta.number), step=1, key="m_number"))
        meta.year = int(st.number_input("Year", value=int(meta.year), step=1, key="m_year"))
        meta.pages = st.text_input("Pages", meta.pages, key="m_pages")
        meta.doi = st.text_input("DOI", meta.doi, key="m_doi")
        meta.received = st.text_input("Received", meta.received, key="m_received")
        meta.revised = st.text_input("Revised", meta.revised, key="m_revised")
        meta.accepted = st.text_input("Accepted", meta.accepted, key="m_accepted")
        meta.published = st.text_input("Published", meta.published, key="m_published")

    st.markdown("**Affiliations**")
    aff_text = st.text_area("One per line", "\n".join(meta.affiliations), height=80, key="m_affs")
    meta.affiliations = [a.strip() for a in aff_text.splitlines() if a.strip()]

    st.markdown("**Authors**")
    max_aff = max(1, len(meta.affiliations))
    for i, a in enumerate(meta.authors):
        with st.expander(f"Author {i + 1}: {a.name or '(blank)'}", expanded=True):
            a.name = st.text_input("Name", a.name, key=f"a{i}_name")
            a.email = st.text_input("Email", a.email or "", key=f"a{i}_email") or None
            a.affiliation_num = int(st.number_input(
                "Affiliation # (1-based index into Affiliations)",
                min_value=1, max_value=max_aff,
                value=min(max(int(a.affiliation_num or 1), 1), max_aff), step=1, key=f"a{i}_aff",
            ))
            a.corresponding = st.checkbox("Corresponding author", a.corresponding, key=f"a{i}_corr")
            a.bio = st.text_area("Bio", a.bio, height=120, key=f"a{i}_bio")

    st.subheader("3. Upload headshots & match authors")
    uploads = st.file_uploader(
        "Headshot image files", type=HEADSHOT_TYPES, accept_multiple_files=True, key=f"headshots_{st.session_state.uploader_epoch}",
    )
    choices = {}   # upload index → author name
    if uploads:
        author_names = [a.name for a in meta.authors if a.name]
        for i, up in enumerate(uploads):
            cols = st.columns([1, 3])
            with cols[0]:
                st.image(up.getvalue(), width=120)
            with cols[1]:
                choice = st.selectbox(
                    f"Which author is {up.name}?", ["(skip)"] + author_names, key=f"hs_{i}",
                )
                if choice != "(skip)":
                    choices[i] = choice

    st.subheader("4. Build starter .docx")
    if st.button("Build cover", type='primary'):
        with st.spinner("Running pipeline…"):
            try:
                headshot_map = {}
                for i, author in choices.items():
                    up = uploads[i]
                    headshot_map[author] = _save_upload(up, "headshots", f"{i}{Path(up.name).suffix}")
                result = run_pipeline(
                    manuscript_src=st.session_state.manuscript_path,
                    headshot_map=headshot_map,
                    meta=meta,
                    work_dir=st.session_state.work_dir / "build",
                )
                st.session_state.starter_bytes = result.starter_path.read_bytes()
                st.success("Cover built. Download below, then continue to Phase 2.")
                if result.no_face_authors:
                    st.warning(
                        "No face was detected in the headshot for: "
                        + ", ".join(result.no_face_authors)
                        + ". The crop used the top of the photo; check it in the starter."
                    )
            except Exception as e:
                st.error(f"Build failed: {e}")
                st.exception(e)

    if st.session_state.starter_bytes:
        st.download_button(
            "Download starter.docx", data=st.session_state.starter_bytes,
            file_name=_output_filename(meta, "starter"), mime=DOCX_MIME,
        )

# =========================================================================
# Phase 2 — Finalize (always available; metadata comes from the starter)
# =========================================================================
st.divider()
st.header("Phase 2 — Finalize proof")

with st.expander("📋 Word paste instructions (read first)", expanded=False):
    st.markdown("""
1. **Open** the starter.docx you downloaded in Microsoft Word.
2. **Open** the author's submitted manuscript in a separate Word window.
3. In the manuscript: **Select all** (⌘A), **Copy** (⌘C).
4. In the starter: scroll to the body section (page 2). Click at the start of
   the placeholder paragraph that reads *"[Paste article body here…]"*.
5. **Paste Special** → **Keep Source Formatting**. On Mac: Edit menu →
   Paste Special → Keep Source Formatting. The placeholder will be replaced
   by your body content.
6. **Delete** any duplicated title, author info, abstract, or keywords that
   the paste brought in at the top of the body — the cover already has them.
   (If you miss some, Phase 2 will try to clean them automatically.)
7. **Save** the file (⌘S — keep the .docx format).
8. **Upload the saved file below.** You can do this in a new browser session;
   the starter carries its own metadata.
    """)

populated = st.file_uploader(
    "Upload your populated starter (after pasting body in Word)", type=['docx'], key=f"populated_upload_{st.session_state.uploader_epoch}",
)

if populated is not None:
    swap_below_captions = st.checkbox(
        "Also try to move any figure/table captions that appear below "
        "their figure/table so they sit above (APA 7).",
        value=False,
        help=(
            "When off (default), below-element captions are reported as warnings "
            "but not modified. When on, the app will attempt to relocate each "
            "caption paragraph above its figure/table after the main fixup pass."
        ),
    )
    if st.button("Finalize proof", type='primary'):
        with st.spinner("Applying TME styles and running fixup battery…"):
            try:
                proof_path = _save_upload(populated, "finalize", "proof.docx")
                meta2, meta_differs = choose_meta(read_meta(proof_path), st.session_state.meta)
                if meta_differs:
                    st.info("Using the metadata carried inside the uploaded starter; "
                            "it differs from this session's Phase 1 values.")
                if meta2 is None:
                    st.error(
                        "This document carries no TME metadata and none is in this session. "
                        "Build the starter again in Phase 1 (newer starters carry it), or "
                        "finalize in the same session you built in."
                    )
                    st.stop()

                style_stats = apply_styles(str(proof_path), meta2)
                fixup_stats = run_fixup(str(proof_path))

                below = fixup_stats.get("captions_below_element", [])
                swapped = 0
                if swap_below_captions and below:
                    from docx import Document as _Doc
                    d = _Doc(str(proof_path))
                    swapped = swap_captions_above(d, below)
                    d.save(str(proof_path))

                final_name = _output_filename(meta2, "proof")
                st.session_state.proof_bytes = proof_path.read_bytes()
                st.session_state.proof_filename = final_name
                st.success("Proof finalized.")

                if style_stats.get("classifier") != "gemini":
                    st.warning(
                        "Gemini did not classify this document "
                        f"({style_stats.get('classifier')}). The heuristic fallback only "
                        "recognizes references, captions and bold headings — expect to "
                        "set H2/H3, lists and block quotes by hand, or fix the API key "
                        "and finalize again."
                    )
                report = style_stats.get("classifier_report") or {}
                if report.get("missing") or report.get("invalid"):
                    st.warning(
                        f"Gemini left {report.get('missing', 0)} paragraph(s) unlabeled and "
                        f"returned {report.get('invalid', 0)} unusable label(s); those were "
                        "styled as body."
                    )
                previews = style_stats.get("deleted_preamble_previews") or []
                if previews:
                    st.info("Removed from the top of the body as cover duplicates:\n\n"
                            + "\n".join(f"- {t}" for t in previews))
                if below:
                    if swap_below_captions:
                        st.info(f"Moved {swapped} of {len(below)} below-element caption(s) above their figure/table.")
                    else:
                        items = "\n".join(f"- {r['kind'].title()} caption: {r['preview']}" for r in below)
                        st.warning(
                            f"{len(below)} caption(s) sit below their figure/table — APA 7 puts "
                            "captions above. Consider toggling the swap checkbox and finalizing "
                            "again, or moving them by hand in Word.\n\n" + items
                        )

                with st.expander("Style + fixup stats"):
                    st.markdown("**apply_styles:**")
                    st.json(style_stats)
                    st.markdown("**fixup:**")
                    st.json(fixup_stats)
            except Exception as e:
                st.error(f"Finalize failed: {e}")
                st.exception(e)

if st.session_state.proof_bytes:
    st.download_button(
        "Download proof.docx", data=st.session_state.proof_bytes,
        file_name=st.session_state.proof_filename, mime=DOCX_MIME,
    )
    st.caption("Open the proof in Word, do a visual pass, then export to PDF (File → Save As → PDF).")
