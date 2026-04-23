"""Streamlit UI for the TME editor app.

Flow:
  Phase 1 — Cover build
    1. Editor uploads manuscript.docx
    2. App extracts text and calls Gemini Flash for structured metadata
    3. Editor reviews / corrects the extracted fields
    4. Editor uploads headshot files and matches each to an author
    5. Click Build → pipeline runs → download starter.docx

  [Manual Word step — see instructions in Phase 2]

  Phase 2 — Finalize proof
    6. Editor opens starter in Word, pastes body (Keep Source Formatting), saves
    7. Editor uploads the populated docx
    8. Click Finalize → apply_styles + fixup run → download proof.docx
"""
import sys
import tempfile
from pathlib import Path

import streamlit as st

# Local packages + sibling build trees
_HERE = Path(__file__).parent
_TME = _HERE.parent
for p in (
    _HERE / 'src',
    _TME / 'template_build' / 'src',
    _TME / 'moore_build' / 'src',
):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

from extractor import ArticleMeta, extract_manuscript_text, extract_metadata
from pipeline import run_pipeline
from apply_styles import apply_styles
from fixup import run_fixup


st.set_page_config(page_title="TME Editor", page_icon="📝", layout="wide")
st.title("The Mathematics Educator — Article Builder")
st.caption(
    "Upload a submitted manuscript and headshots. The app extracts metadata "
    "with Gemini, lets you review it, then builds a formatted starter .docx. "
    "After pasting the body in Word, come back to finalize into a proof."
)

# --- Session state ---
for key, default in (
    ("meta", None),
    ("manuscript_path", None),
    ("starter_path", None),
    ("starter_bytes", None),
    ("proof_bytes", None),
    ("proof_filename", None),
):
    if key not in st.session_state:
        st.session_state[key] = default


def _save_upload(uploaded, suffix: str) -> Path:
    path = Path(tempfile.mkdtemp()) / f"upload{suffix}"
    path.write_bytes(uploaded.getvalue())
    return path


def _proof_filename(meta) -> str:
    last = "Author"
    if meta.authors and meta.authors[0].name:
        last = meta.authors[0].name.rsplit(" ", 1)[-1]
    # Strip characters that are iffy in filenames
    last = "".join(c for c in last if c.isalnum() or c in "-_")
    return f"TME_{last}_{meta.year}_proof.docx"


def _starter_filename(meta) -> str:
    last = "Author"
    if meta.authors and meta.authors[0].name:
        last = meta.authors[0].name.rsplit(" ", 1)[-1]
    last = "".join(c for c in last if c.isalnum() or c in "-_")
    return f"TME_{last}_{meta.year}_starter.docx"


# =========================================================================
# Phase 1 — Cover build
# =========================================================================

st.header("Phase 1 — Cover build")

st.subheader("1. Upload manuscript")
ms = st.file_uploader("Submitted manuscript (.docx)", type=['docx'], key='ms_upload')
if ms is not None and st.session_state.manuscript_path is None:
    st.session_state.manuscript_path = _save_upload(ms, '.docx')

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
        meta.title = st.text_area("Title", meta.title, height=80)
        meta.abstract = st.text_area("Abstract", meta.abstract, height=200)
        meta.keywords = [k.strip() for k in st.text_input(
            "Keywords (comma-separated)", ", ".join(meta.keywords)
        ).split(",") if k.strip()]
    with col2:
        meta.volume = st.number_input("Volume", value=meta.volume, step=1)
        meta.number = st.number_input("Number", value=meta.number, step=1)
        meta.year = st.number_input("Year", value=meta.year, step=1)
        meta.pages = st.text_input("Pages", meta.pages)
        meta.doi = st.text_input("DOI", meta.doi)
        meta.received = st.text_input("Received", meta.received)
        meta.revised = st.text_input("Revised", meta.revised)
        meta.accepted = st.text_input("Accepted", meta.accepted)
        meta.published = st.text_input("Published", meta.published)

    st.markdown("**Affiliations**")
    aff_text = st.text_area(
        "One per line",
        "\n".join(meta.affiliations),
        height=80,
    )
    meta.affiliations = [a.strip() for a in aff_text.splitlines() if a.strip()]

    st.markdown("**Authors**")
    for i, a in enumerate(meta.authors):
        with st.expander(f"Author {i + 1}: {a.name or '(blank)'}", expanded=True):
            a.name = st.text_input("Name", a.name, key=f"a{i}_name")
            a.email = st.text_input("Email", a.email or "", key=f"a{i}_email") or None
            a.affiliation_num = st.number_input(
                "Affiliation # (1-based index into Affiliations)",
                value=a.affiliation_num, step=1, key=f"a{i}_aff",
            )
            a.corresponding = st.checkbox(
                "Corresponding author", a.corresponding, key=f"a{i}_corr"
            )
            a.bio = st.text_area("Bio", a.bio, height=120, key=f"a{i}_bio")

    st.subheader("3. Upload headshots & match authors")
    uploads = st.file_uploader(
        "Headshot image files (any common format)",
        type=['jpg', 'jpeg', 'png', 'avif', 'webp'],
        accept_multiple_files=True,
        key='headshots',
    )
    headshot_map = {}
    if uploads:
        author_names = [a.name for a in meta.authors if a.name]
        for up in uploads:
            cols = st.columns([1, 3])
            with cols[0]:
                st.image(up.getvalue(), width=120)
            with cols[1]:
                choice = st.selectbox(
                    f"Which author is {up.name}?",
                    ["(skip)"] + author_names,
                    key=f"hs_{up.name}",
                )
                if choice != "(skip)":
                    headshot_map[choice] = _save_upload(up, Path(up.name).suffix)

    st.subheader("4. Build starter .docx")
    if st.button("Build cover", type='primary'):
        with st.spinner("Running pipeline…"):
            try:
                work_dir = Path(tempfile.mkdtemp())
                out_path = run_pipeline(
                    manuscript_src=st.session_state.manuscript_path,
                    headshot_map=headshot_map,
                    meta=meta,
                    work_dir=work_dir,
                )
                st.session_state.starter_path = out_path
                st.session_state.starter_bytes = out_path.read_bytes()
                st.success("Cover built. Download below, then continue to Phase 2.")
            except Exception as e:
                st.error(f"Build failed: {e}")
                st.exception(e)

    if st.session_state.starter_bytes:
        st.download_button(
            "Download starter.docx",
            data=st.session_state.starter_bytes,
            file_name=_starter_filename(meta),
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    # =====================================================================
    # Phase 2 — Finalize
    # =====================================================================
    if st.session_state.starter_bytes:
        st.divider()
        st.header("Phase 2 — Finalize proof")

        with st.expander("📋 Word paste instructions (read first)", expanded=True):
            st.markdown("""
1. **Open** the starter.docx you just downloaded in Microsoft Word.
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
8. **Upload the saved file below.**
            """)

        populated = st.file_uploader(
            "Upload your populated starter (after pasting body in Word)",
            type=['docx'],
            key='populated_upload',
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
                        work_dir = Path(tempfile.mkdtemp())
                        proof_path = work_dir / _proof_filename(meta)
                        proof_path.write_bytes(populated.getvalue())

                        style_stats = apply_styles(str(proof_path), meta)
                        fixup_stats = run_fixup(str(proof_path))

                        # Opt-in swap of below-element captions
                        below = fixup_stats.get("captions_below_element", [])
                        swapped = 0
                        if swap_below_captions and below:
                            from docx import Document as _Doc
                            from fixup import swap_captions_above
                            d = _Doc(str(proof_path))
                            swapped = swap_captions_above(d, below)
                            d.save(str(proof_path))

                        st.session_state.proof_bytes = proof_path.read_bytes()
                        st.session_state.proof_filename = _proof_filename(meta)

                        st.success("Proof finalized.")

                        # APA-7 caption position warning
                        if below:
                            if swap_below_captions:
                                st.info(
                                    f"Moved {swapped} of {len(below)} below-element "
                                    "caption(s) above their figure/table."
                                )
                            else:
                                items = "\n".join(
                                    f"- {r['kind'].title()} caption: {r['preview']}"
                                    for r in below
                                )
                                st.warning(
                                    f"{len(below)} caption(s) sit below their figure/"
                                    "table — APA 7 puts captions above. Consider "
                                    "toggling the swap checkbox and finalizing again, "
                                    "or moving them by hand in Word.\n\n" + items
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
                "Download proof.docx",
                data=st.session_state.proof_bytes,
                file_name=st.session_state.proof_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            st.caption(
                "Open the proof in Word, do a visual pass, then export to PDF "
                "(File → Save As → PDF)."
            )
