# TME template post-Moore-proof changes — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply seven template-level changes captured in `docs/superpowers/specs/2026-04-23-tme-template-post-moore-proof-design.md` — title/tagline spacing, cover reorder, body-footer simplification, APA-7 captions, 5-step grayscale palette, H3 bold — and regenerate the Moore proof.

**Architecture:** Two Python packages under one deploy repo (`tme-editor/`). `template_build/src/tme_template/` holds cover/masthead/styles/color code used by both the live editor and the template-docx builder. `tme_editor_app/src/` holds the Streamlit flow and fixup battery. No new modules; one new `tests/` subtree under `template_build/`. All changes are additive or in-place edits.

**Tech Stack:** Python 3.11+, `python-docx`, `lxml`, `streamlit`, `pytest`. Package install via editable `-e` requirement lines already present in `requirements.txt`.

**Working assumption:** You are working directly on `main` in `/Users/jenniferkleiman/Documents/tme-editor/`. No worktree. Commits happen on main. After the final task lands, mirror the updated files back to `/Users/jenniferkleiman/Documents/tme/` so Jennifer's scratch tree is in sync.

**Convention:** Commit subjects are sentence-case, colon-separated. No `feat:` / `fix:` prefixes (match existing repo history). Every commit ends with:

```
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

---

## File structure

Files created:

- `template_build/tests/__init__.py` — empty, marks tests as a package
- `template_build/tests/conftest.py` — pytest config (adds `src/` to path)
- `template_build/tests/test_colors.py` — asserts palette constants
- `template_build/tests/test_styles_updates.py` — asserts new style properties (Title spacing, H3 bold, caption alignment)
- `template_build/tests/test_cover_page_order.py` — asserts ABOUT THE AUTHORS precedes ABSTRACT
- `template_build/tests/test_headers_footers_update.py` — asserts page-number-only body footer
- `tme_editor_app/tests/__init__.py` — empty
- `tme_editor_app/tests/test_fixup_captions.py` — asserts new caption functions

Files modified:

- `template_build/src/tme_template/colors.py` — new palette
- `template_build/src/tme_template/styles.py` — Title spacing, H3 bold, caption alignment, palette constants
- `template_build/src/tme_template/cover_page.py` — reorder blocks, palette constants
- `template_build/src/tme_template/cover_footer.py` — palette constants
- `template_build/src/tme_template/masthead.py` — palette constants
- `template_build/src/tme_template/tagline.py` — palette constants
- `template_build/src/tme_template/headers_footers.py` — footer simplification, palette constants
- `template_build/src/tme_template/front_matter.py` — palette constants
- `template_build/src/build_template.py` — drop `copyright_line` argument to `set_running_footer`
- `tme_editor_app/src/fixup.py` — caption style updates, remove `glue_figures_to_captions`, add `report_below_element_captions`, add `swap_captions_above`
- `tme_editor_app/src/article_starter.py` — drop `copyright_line` argument to `set_running_footer`
- `tme_editor_app/app.py` — surface caption-below-element warnings + opt-in swap checkbox

Generated artifact regenerated at the end:

- `TME_Template_2026.docx` (top of repo)

---

## Task 1: Bootstrap test infrastructure

**Files:**
- Create: `template_build/tests/conftest.py`
- Create: `tme_editor_app/tests/conftest.py`

Note: no `__init__.py` in either tests/ directory. With `__init__.py`, pytest's
default importer treats both `conftest.py` files as `tests.conftest` at the top
level and refuses to load the second one. Keeping tests/ as a non-package
directory makes both conftest files loadable together.

- [ ] **Step 1: (no-op; __init__.py files are intentionally not created)**

- [ ] **Step 2: Write `template_build/tests/conftest.py`**

```python
"""Pytest config — ensure the tme_template package is importable."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
```

- [ ] **Step 3: Write `tme_editor_app/tests/conftest.py`**

```python
"""Pytest config — ensure editor-app src and sibling packages are importable."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parent
for p in (HERE / "src", REPO / "template_build" / "src", REPO / "moore_build" / "src"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)
```

- [ ] **Step 4: Verify pytest can discover the new dirs**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python3 -m pytest template_build/tests tme_editor_app/tests --collect-only -q`
Expected: "no tests collected" (no test files yet) with no import errors.

- [ ] **Step 5: Commit**

```bash
git add template_build/tests/conftest.py tme_editor_app/tests/conftest.py
git commit -m "$(cat <<'EOF'
Bootstrap pytest dirs for template_build and editor app

Adds a conftest.py in each package's tests/ directory that prepends the
relevant src/ paths to sys.path. No tests/__init__.py — pytest's default
importer rejects duplicate top-level module names across two such dirs,
and we don't need package semantics for the test tree.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: New 5-step grayscale palette in colors.py

**Files:**
- Modify: `template_build/src/tme_template/colors.py`
- Create: `template_build/tests/test_colors.py`

- [ ] **Step 1: Write the failing test**

Write `template_build/tests/test_colors.py`:

```python
"""Assert the deliberate 5-step grayscale palette is present with correct values."""
from tme_template import colors


def test_palette_grays_defined():
    assert colors.INK == "111111"
    assert colors.BLOCKQUOTE_INK == "333333"
    assert colors.TEXT_MUTED == "444444"
    assert colors.META == "777777"
    assert colors.LINE == "BBBBBB"


def test_palette_accents_defined():
    assert colors.UGA_RED == "BA0C2F"
    assert colors.BLACK == "000000"
    assert colors.LIGHT_PANEL_GRAY == "F5F5F5"
    assert colors.FOOTER_CREAM == "FAFAF7"


def test_deprecation_aliases_resolve_to_new_palette():
    # Deprecated aliases are kept through the migration so tagline.py and any
    # other importer keeps working until Task 12 removes each usage. Final
    # removal happens at the end of the migration (Task 12h).
    assert colors.TAGLINE_GRAY == colors.META
    assert colors.RULE_GRAY == colors.LINE
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests/test_colors.py -v`
Expected: `test_palette_grays_defined` FAILS with `AttributeError: module 'tme_template.colors' has no attribute 'INK'`.

- [ ] **Step 3: Rewrite `colors.py`**

Replace the full contents of `template_build/src/tme_template/colors.py`:

```python
"""Deliberate color palette for TME digital template.

Hex strings WITHOUT leading #, as required by python-docx shading API.
See docs/superpowers/specs/2026-04-23-tme-template-post-moore-proof-design.md
§"Deliberate 5-step grayscale palette".
"""

# Accents
UGA_RED = "BA0C2F"
BLACK = "000000"

# 5-step grayscale (deliberate; do not add new shades without updating the spec)
INK = "111111"             # Title, H1, H2, H3, body text
BLOCKQUOTE_INK = "333333"  # TME Block Quote only — intentionally a touch lighter than body
TEXT_MUTED = "444444"      # captions, footnote, cover-footer text, page number, issue credit
META = "777777"            # dates, affiliations, tagline italic, running-footer meta,
                           # front-matter role labels
LINE = "BBBBBB"            # cover rules, date separators, footer top rule

# Panels (non-text)
LIGHT_PANEL_GRAY = "F5F5F5"  # tagline strip background
FOOTER_CREAM = "FAFAF7"      # cover footer background

# ---------- Deprecated aliases (remove after Task 12 migration completes) ----------
# Kept so existing callers continue to import successfully during the refactor.
# Task 12h removes these and flips the test to assert they are gone.
TAGLINE_GRAY = META   # deprecated — callers migrate to META
RULE_GRAY = LINE      # deprecated — callers migrate to LINE
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests/test_colors.py -v`
Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add template_build/src/tme_template/colors.py template_build/tests/test_colors.py
git commit -m "$(cat <<'EOF'
Introduce deliberate 5-step palette; keep old names as aliases

colors.py now exposes INK / BLOCKQUOTE_INK / TEXT_MUTED / META / LINE as
the deliberate grayscale. TAGLINE_GRAY and RULE_GRAY remain as
deprecated aliases so call sites keep importing until Task 12 migrates
each file. Task 12h removes the aliases.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Update TME Title spacing

**Files:**
- Modify: `template_build/src/tme_template/styles.py:27-37`
- Create: `template_build/tests/test_styles_updates.py`

- [ ] **Step 1: Write the failing test**

Write `template_build/tests/test_styles_updates.py`:

```python
"""Assert the post-Moore-proof style updates land correctly."""
from docx import Document
from docx.shared import Pt

from tme_template.styles import (
    register_title_style,
    register_heading_styles,
    register_remaining_styles,
)


def test_title_has_12pt_space_before():
    doc = Document()
    register_title_style(doc)
    style = doc.styles["TME Title"]
    assert style.paragraph_format.space_before == Pt(12)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests/test_styles_updates.py::test_title_has_12pt_space_before -v`
Expected: FAIL — current value is `Pt(0)`.

- [ ] **Step 3: Update `register_title_style` in `styles.py`**

In `template_build/src/tme_template/styles.py`, change the `register_title_style` function:

```python
def register_title_style(doc) -> None:
    style = _get_or_add_paragraph_style(doc, "TME Title")
    style.font.name = "Georgia"
    style.font.size = Pt(18)
    style.font.bold = True
    style.font.color.rgb = RGBColor(0x11, 0x11, 0x11)
    pf = style.paragraph_format
    pf.line_spacing = 1.15
    pf.space_before = Pt(12)   # was Pt(0); adds breathing room below the tagline strip
    pf.space_after = Pt(10)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests/test_styles_updates.py::test_title_has_12pt_space_before -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add template_build/src/tme_template/styles.py template_build/tests/test_styles_updates.py
git commit -m "$(cat <<'EOF'
TME Title: add 12pt space-before for tagline breathing room

Combined with the tagline strip's 4pt space-after, the cover title now
opens with a 16pt gap — matching the existing 8+8pt rhythm around the
dates row.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: TME H3 becomes bold, not italic

**Files:**
- Modify: `template_build/src/tme_template/styles.py:64-74`
- Modify: `template_build/tests/test_styles_updates.py`

- [ ] **Step 1: Add the failing tests**

Append to `template_build/tests/test_styles_updates.py`:

```python
def test_h3_is_bold_not_italic():
    doc = Document()
    register_heading_styles(doc)
    h3 = doc.styles["TME H3"]
    assert h3.font.bold is True
    assert h3.font.italic is False


def test_h1_and_h2_italicization_unchanged():
    doc = Document()
    register_heading_styles(doc)
    h1 = doc.styles["TME H1"]
    h2 = doc.styles["TME H2"]
    assert h1.font.bold is True and h1.font.italic is not True
    assert h2.font.bold is True and h2.font.italic is True
```

- [ ] **Step 2: Run the new tests to verify `test_h3_is_bold_not_italic` fails**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests/test_styles_updates.py -v`
Expected: `test_h3_is_bold_not_italic` FAILS (`h3.font.bold` is `False`), `test_h1_and_h2_italicization_unchanged` PASSES.

- [ ] **Step 3: Update H3 in `register_heading_styles`**

In `template_build/src/tme_template/styles.py`, change the H3 block:

```python
    h3 = _get_or_add_paragraph_style(doc, "TME H3")
    h3.font.name = "Georgia"
    h3.font.size = Pt(11.5)
    h3.font.bold = True    # was False
    h3.font.italic = False # was True
    h3.font.color.rgb = RGBColor(0x33, 0x33, 0x33)  # palette migration handles this in Task 12
    h3.paragraph_format.space_before = Pt(10)
    h3.paragraph_format.space_after = Pt(4)
    h3.paragraph_format.keep_with_next = True
    h3.paragraph_format.keep_together = True
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests/test_styles_updates.py -v`
Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add template_build/src/tme_template/styles.py template_build/tests/test_styles_updates.py
git commit -m "$(cat <<'EOF'
TME H3: switch to bold, drop italic

Aligns H3 with APA 7 and establishes a clean hierarchy: H1 bold, H2
bold italic, H3 bold. No italic-only heads remain in the template.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Caption styles — left-aligned, keep-with-next; remove stale comment

**Files:**
- Modify: `template_build/src/tme_template/styles.py:76-95`
- Modify: `template_build/tests/test_styles_updates.py`

- [ ] **Step 1: Add the failing tests**

Append to `template_build/tests/test_styles_updates.py`:

```python
from docx.enum.text import WD_ALIGN_PARAGRAPH


def test_figure_caption_is_left_aligned_and_sticky():
    doc = Document()
    register_remaining_styles(doc)
    fc = doc.styles["TME Figure Caption"]
    assert fc.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.LEFT
    assert fc.paragraph_format.keep_with_next is True


def test_table_caption_is_left_aligned_and_sticky():
    doc = Document()
    register_remaining_styles(doc)
    tc = doc.styles["TME Table Caption"]
    assert tc.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.LEFT
    assert tc.paragraph_format.keep_with_next is True
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests/test_styles_updates.py -v`
Expected: the two caption tests FAIL — current alignment is CENTER, `TME Figure Caption` has no `keep_with_next`.

- [ ] **Step 3: Update `register_remaining_styles` caption blocks**

In `template_build/src/tme_template/styles.py`, replace the figure-caption and table-caption blocks:

```python
def register_remaining_styles(doc) -> None:
    # APA 7: figure and table captions both sit ABOVE their element, flush left.
    # keep_with_next on the caption itself glues it to the figure/table below.
    fc = _get_or_add_paragraph_style(doc, "TME Figure Caption")
    fc.font.name = "Georgia"
    fc.font.size = Pt(10)
    fc.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
    fc.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    fc.paragraph_format.space_before = Pt(18)
    fc.paragraph_format.space_after = Pt(6)
    fc.paragraph_format.keep_with_next = True

    tc = _get_or_add_paragraph_style(doc, "TME Table Caption")
    tc.font.name = "Georgia"
    tc.font.size = Pt(10)
    tc.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
    tc.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    tc.paragraph_format.space_before = Pt(18)
    tc.paragraph_format.space_after = Pt(6)
    tc.paragraph_format.keep_with_next = True
```

Then continue the rest of the function (footnote, reference, pullquote, block quote, list paragraph) unchanged.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests/test_styles_updates.py -v`
Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add template_build/src/tme_template/styles.py template_build/tests/test_styles_updates.py
git commit -m "$(cat <<'EOF'
Captions: flush left, keep-with-next, both above their element (APA 7)

Both TME Figure Caption and TME Table Caption now set
alignment=LEFT and keep_with_next=True. The style itself carries the
stickiness to the following figure/table. Fixup will stop gluing
figures to captions below them (see next commit).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Reorder cover — ABOUT THE AUTHORS before ABSTRACT

**Files:**
- Modify: `template_build/src/tme_template/cover_page.py:135-229`
- Create: `template_build/tests/test_cover_page_order.py`

- [ ] **Step 1: Write the failing test**

Write `template_build/tests/test_cover_page_order.py`:

```python
"""Assert About-the-Authors comes before Abstract on the cover page."""
from docx import Document

from tme_template.cover_page import AuthorEntry, CoverData, add_research_article_cover
from tme_template.styles import (
    register_body_style, register_title_style,
    register_heading_styles, register_remaining_styles,
)


def _build_sample_cover():
    doc = Document()
    register_body_style(doc)
    register_title_style(doc)
    register_heading_styles(doc)
    register_remaining_styles(doc)
    add_research_article_cover(doc, CoverData(
        title="Sample Title",
        authors=[
            AuthorEntry(name="Ada Lovelace", affiliation_num=1, role=None,
                        bio="Mathematician.", headshot_path=None,
                        corresponding=True, email="ada@example.edu"),
            AuthorEntry(name="Grace Hopper", affiliation_num=1, role=None,
                        bio="Computer scientist.", headshot_path=None,
                        corresponding=False, email=None),
        ],
        affiliations=["Example University"],
        dates={"Received": "Jan 1", "Revised": "Feb 1",
               "Accepted": "Mar 1", "Published": "2026"},
        abstract="This is the abstract.",
        keywords=["alpha", "beta"],
    ))
    return doc


def _first_index_of(doc, text_fragment: str) -> int:
    for i, p in enumerate(doc.paragraphs):
        if text_fragment in p.text:
            return i
    raise AssertionError(f"'{text_fragment}' not found in cover")


def test_about_the_authors_precedes_abstract():
    doc = _build_sample_cover()
    about_idx = _first_index_of(doc, "ABOUT THE AUTHORS")
    abstract_idx = _first_index_of(doc, "ABSTRACT")
    assert about_idx < abstract_idx, (
        f"Expected ABOUT THE AUTHORS (idx {about_idx}) before ABSTRACT "
        f"(idx {abstract_idx})"
    )


def test_abstract_precedes_keywords():
    doc = _build_sample_cover()
    abstract_idx = _first_index_of(doc, "ABSTRACT")
    keywords_idx = _first_index_of(doc, "Keywords:")
    assert abstract_idx < keywords_idx
```

- [ ] **Step 2: Run test to verify `test_about_the_authors_precedes_abstract` fails**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests/test_cover_page_order.py -v`
Expected: `test_about_the_authors_precedes_abstract` FAILS; `test_abstract_precedes_keywords` passes.

- [ ] **Step 3: Reorder blocks in `add_research_article_cover`**

In `template_build/src/tme_template/cover_page.py`, the current order of the final three blocks is (lines roughly 129–229):

1. Rule
2. ABSTRACT label + text + keywords
3. Rule
4. ABOUT THE AUTHORS label + 3-col author table

Change to:

1. Rule
2. ABOUT THE AUTHORS label + 3-col author table
3. Rule
4. ABSTRACT label + text + keywords

Concretely — the block that starts with:

```python
    # Abstract label and text
    lbl = doc.add_paragraph()
```

should move **after** the `# Author block — 3-column table (one cell per author)` block. The two `apply_bottom_rule` rules swap positions accordingly. Do not change any spacing constants inside the individual blocks; only move them. The final structure of the function body should read (abbreviated — inner code unchanged):

```python
def add_research_article_cover(doc, data: CoverData) -> None:
    # Title
    ...
    # Authors line
    ...
    # Affiliations
    ...
    # Corresponding author line
    ...
    # Dates row
    ...
    # Rule 1
    rule_p = doc.add_paragraph()
    rule_p.paragraph_format.space_before = Pt(0)
    rule_p.paragraph_format.space_after = Pt(8)
    apply_bottom_rule(rule_p, hex_color="CCCCCC", width_pt=1)

    # ABOUT THE AUTHORS label
    ab_lbl = doc.add_paragraph()
    ab_lbl.paragraph_format.space_before = Pt(0)
    ab_lbl.paragraph_format.space_after = Pt(4)
    _red_label(ab_lbl, "ABOUT THE AUTHORS")

    # Author block — 3-column table (existing loop unchanged)
    n = len(data.authors)
    col_width = Inches(7.5 / n)
    tbl = doc.add_table(rows=1, cols=n)
    tbl.style = "Table Grid"
    row = tbl.rows[0]
    trPr = row._tr.get_or_add_trPr()
    cantSplit = OxmlElement('w:cantSplit')
    trPr.append(cantSplit)
    for col_idx, a in enumerate(data.authors):
        # (body of the loop unchanged — headshot, name, bio)
        ...

    # Rule 2
    rule_p2 = doc.add_paragraph()
    rule_p2.paragraph_format.space_before = Pt(0)
    rule_p2.paragraph_format.space_after = Pt(8)
    apply_bottom_rule(rule_p2, hex_color="CCCCCC", width_pt=1)

    # Abstract label
    lbl = doc.add_paragraph()
    lbl.paragraph_format.space_before = Pt(0)
    lbl.paragraph_format.space_after = Pt(4)
    _red_label(lbl, "ABSTRACT")

    # Abstract text
    ab = doc.add_paragraph()
    ab.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    ab.paragraph_format.space_before = Pt(0)
    ab.paragraph_format.space_after = Pt(6)
    ab.paragraph_format.line_spacing = 1.3
    ab_run = ab.add_run(data.abstract)
    ab_run.font.name = "Georgia"
    ab_run.font.size = Pt(10)

    # Keywords (unchanged)
    kw = doc.add_paragraph()
    ...
```

Make the change by moving the relevant paragraphs; do not duplicate any block. If you change rule hex colors or spacing here, stop — that is Task 12's concern.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests/test_cover_page_order.py -v`
Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add template_build/src/tme_template/cover_page.py template_build/tests/test_cover_page_order.py
git commit -m "$(cat <<'EOF'
Cover: move "About the Authors" above the abstract

Editor preferred ordering after the Moore proof review. The author
block (headshots + bios) now follows the dates rule and precedes the
ABSTRACT block. Rule positions swap with the reorder; no spacing
constants change.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Body running footer = page number only

**Files:**
- Modify: `template_build/src/tme_template/headers_footers.py:60-115`
- Create: `template_build/tests/test_headers_footers_update.py`

- [ ] **Step 1: Write the failing test**

Write `template_build/tests/test_headers_footers_update.py`:

```python
"""Assert the body running footer is just a centered page number."""
from docx import Document
from docx.oxml.ns import qn

from tme_template.headers_footers import set_running_footer


def _footer_text(section):
    parts = []
    for p in section.footer.paragraphs:
        parts.append(p.text)
    return " | ".join(parts)


def _footer_has_page_field(section):
    """Search the footer XML for a PAGE field instruction."""
    xml = section.footer._element.xml
    return 'PAGE' in xml and 'w:fldChar' in xml


def test_footer_has_no_copyright_text():
    doc = Document()
    section = doc.sections[0]
    set_running_footer(doc, section=section)
    txt = _footer_text(section)
    assert "©" not in txt
    assert "CC BY" not in txt
    assert "Authors" not in txt


def test_footer_contains_page_field():
    doc = Document()
    section = doc.sections[0]
    set_running_footer(doc, section=section)
    assert _footer_has_page_field(section)


def test_footer_paragraph_is_centered():
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    doc = Document()
    section = doc.sections[0]
    set_running_footer(doc, section=section)
    assert section.footer.paragraphs[0].alignment == WD_ALIGN_PARAGRAPH.CENTER
```

- [ ] **Step 2: Run test to verify failures**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests/test_headers_footers_update.py -v`
Expected: the first test will either FAIL (because the current `set_running_footer` requires `copyright_line` as a positional argument) or error with `TypeError`. Either counts as red.

- [ ] **Step 3: Update `set_running_footer` and `_build_footer`**

Replace the bottom half of `template_build/src/tme_template/headers_footers.py` (everything from `_build_footer` down):

```python
def _build_footer(container):
    """Centered page number with a 1pt top rule. Same layout on verso and recto."""
    _clear(container)
    p = container.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    apply_top_rule(p, hex_color="EEEEEE", width_pt=1)  # palette migration in Task 12
    run = p.add_run()
    run.font.name = "Georgia"
    run.font.size = Pt(9.5)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x22, 0x22, 0x22)  # palette migration in Task 12
    _add_page_field(run)


def set_running_footer(doc, section=None) -> None:
    """Body-page footer: centered page number only. No copyright, no license line.

    If *section* is provided, operate only on that section object.
    When None (default), operate on all sections (backward-compatible).
    """
    if section is not None:
        section.footer.is_linked_to_previous = False
        section.even_page_footer.is_linked_to_previous = False
    sections = [section] if section is not None else doc.sections
    for sec in sections:
        _build_footer(sec.footer)
        _build_footer(sec.even_page_footer)
```

(Leave `_add_page_field`, `_add_italic_gray_line`, `_clear`, and `set_running_headers` above untouched.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests/test_headers_footers_update.py -v`
Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add template_build/src/tme_template/headers_footers.py template_build/tests/test_headers_footers_update.py
git commit -m "$(cat <<'EOF'
Body footer: drop copyright+license, keep centered page number

The per-article © line repeated on every body page was redundant with
the cover footer's official notice. The body running footer now emits
a single centered PAGE field with the same 1pt top rule for visual
separation. set_running_footer's copyright_line parameter is removed;
callers are updated next.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Update callers of `set_running_footer`

**Files:**
- Modify: `tme_editor_app/src/article_starter.py:133-135`
- Modify: `template_build/src/build_template.py:148-150`

- [ ] **Step 1: Update `tme_editor_app/src/article_starter.py`**

Find:

```python
    set_running_footer(doc,
        copyright_line=f"© {meta.year} The Authors  ·  CC BY 4.0",
        section=body_section)
```

Replace with:

```python
    set_running_footer(doc, section=body_section)
```

- [ ] **Step 2: Update `template_build/src/build_template.py`**

Find:

```python
    set_running_footer(doc,
        copyright_line="© 2026 The Authors  ·  CC BY 4.0",
        section=body_section)
```

Replace with:

```python
    set_running_footer(doc, section=body_section)
```

- [ ] **Step 3: Run all template tests to catch regressions**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests -v`
Expected: everything passes. In particular, `test_headers_footers_update.py` still passes and nothing else calls the removed parameter.

- [ ] **Step 4: Syntax-check the two edited files**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m py_compile tme_editor_app/src/article_starter.py template_build/src/build_template.py`
Expected: no output, no error. (`py_compile` validates syntax without executing imports, so it doesn't depend on the palette migration being complete.)

- [ ] **Step 5: Commit**

```bash
git add tme_editor_app/src/article_starter.py template_build/src/build_template.py
git commit -m "$(cat <<'EOF'
Drop copyright_line from set_running_footer callers

article_starter and build_template now invoke the simplified footer
signature. No behavior change beyond what the previous commit made.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Fixup — remove `glue_figures_to_captions`, update caption style updates

**Files:**
- Modify: `tme_editor_app/src/fixup.py`

Rationale: captions now sit above their elements with `keep_with_next` on the caption itself (Task 5). The old `glue_figures_to_captions` function set `keep_with_next` on the paragraph *above* a figure caption under the assumption captions were below — that's wrong now and will cause regular body paragraphs to glue to captions.

- [ ] **Step 1: Delete `glue_figures_to_captions` and its helper**

In `tme_editor_app/src/fixup.py`:

- Remove the entire `glue_figures_to_captions` function (currently lines ~178-202).
- Remove the entire `_paragraph_has_image` helper (currently lines ~205-207) — we will add a new image-detect helper in Task 10 if needed, scoped to the new behavior.

- [ ] **Step 2: Update `update_styles` caption blocks**

In `update_styles` (around lines 56-64), replace the figure/table caption code:

```python
    fc = styles["TME Figure Caption"]
    fc.font.name = "Georgia"
    fc.paragraph_format.keep_with_next = True  # caption above → glue down to figure/table

    tc = styles["TME Table Caption"]
    tc.font.name = "Georgia"
    tc.paragraph_format.keep_with_next = True
```

Delete the now-incorrect multi-line comment that says "Figure captions go BELOW figures — we glue the FIGURE paragraph to the caption below". It is gone with the code.

- [ ] **Step 3: Remove the `glue_figures_to_captions` call and `figures_glued` entry from `run_fixup`**

Change `run_fixup` from:

```python
    caption_stats = fix_caption_classifications(doc)
    list_n = clear_list_direct_spacing(doc)
    fig_glued = glue_figures_to_captions(doc)
    t_count = fix_content_tables(doc)
```

to:

```python
    caption_stats = fix_caption_classifications(doc)
    list_n = clear_list_direct_spacing(doc)
    t_count = fix_content_tables(doc)
```

And in the return dict, remove the `"figures_glued": fig_glued,` line.

- [ ] **Step 4: Run the existing fixup-adjacent sanity check**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -c "from tme_editor_app.src.fixup import run_fixup"` (if that fails due to package layout, run: `cd /Users/jenniferkleiman/Documents/tme-editor/tme_editor_app/src && python -c "import fixup; print([n for n in dir(fixup) if 'glue' in n])"`)
Expected: `[]` — no `glue_figures_to_captions` left in the module.

- [ ] **Step 5: Commit**

```bash
git add tme_editor_app/src/fixup.py
git commit -m "$(cat <<'EOF'
Fixup: drop glue_figures_to_captions; captions carry their own keep-next

Captions are now above their element (APA 7, Task 5) with
keep_with_next set on the caption style itself. The old glue function
was setting keep_with_next on the paragraph above a caption, which
would misglue ordinary body text to captions under the new ordering.
Caption style updates in update_styles also drop the stale
keep_with_next on TME Table Caption only — both caption styles carry
it now.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Add `report_below_element_captions` to fixup.py

**Files:**
- Modify: `tme_editor_app/src/fixup.py`
- Create: `tme_editor_app/tests/test_fixup_captions.py`

- [ ] **Step 1: Write the failing test**

Write `tme_editor_app/tests/test_fixup_captions.py`:

```python
"""Tests for the new caption-below-element detection and swap helpers."""
from docx import Document
from docx.oxml.ns import qn

import fixup
from apply_styles import apply_styles  # noqa: F401  (register side effects not needed here)
from tme_template.styles import (
    register_body_style, register_title_style,
    register_heading_styles, register_remaining_styles,
)


def _make_doc_with_styles():
    doc = Document()
    register_body_style(doc)
    register_title_style(doc)
    register_heading_styles(doc)
    register_remaining_styles(doc)
    return doc


def _add_fake_drawing_paragraph(doc):
    """Add a paragraph whose XML contains a w:drawing element so the detector
    treats it as an image-bearing paragraph without needing real image bytes."""
    p = doc.add_paragraph("", style="TME Body")
    from docx.oxml import OxmlElement
    run = p.add_run()
    drawing = OxmlElement("w:drawing")
    run._r.append(drawing)
    return p


def test_report_flags_figure_caption_below_drawing():
    doc = _make_doc_with_styles()
    # figure-above-caption pattern (APA-correct): no report
    doc.add_paragraph("Figure 1. A thing.", style="TME Figure Caption")
    _add_fake_drawing_paragraph(doc)
    # caption-below-drawing pattern (flag this)
    _add_fake_drawing_paragraph(doc)
    doc.add_paragraph("Figure 2. Another thing.", style="TME Figure Caption")
    result = fixup.report_below_element_captions(doc)
    kinds = [r["kind"] for r in result]
    assert kinds == ["figure"]
    assert "Figure 2" in result[0]["preview"]


def test_report_flags_table_caption_below_table():
    doc = _make_doc_with_styles()
    # caption-above-table (correct): no report
    doc.add_paragraph("Table 1. Correct position.", style="TME Table Caption")
    doc.add_table(rows=2, cols=2)
    # table-above-caption (flag)
    doc.add_table(rows=2, cols=2)
    doc.add_paragraph("Table 2. Wrong position.", style="TME Table Caption")
    result = fixup.report_below_element_captions(doc)
    kinds = [r["kind"] for r in result]
    assert kinds == ["table"]
    assert "Table 2" in result[0]["preview"]


def test_run_fixup_returns_captions_below_element_key():
    doc = _make_doc_with_styles()
    _add_fake_drawing_paragraph(doc)
    doc.add_paragraph("Figure 1. Below.", style="TME Figure Caption")
    # Save to a temp path, run fixup, check the stats dict
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "t.docx"
        doc.save(str(path))
        stats = fixup.run_fixup(str(path))
    assert "captions_below_element" in stats
    assert isinstance(stats["captions_below_element"], list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest tme_editor_app/tests/test_fixup_captions.py -v`
Expected: all three tests FAIL (`AttributeError: module 'fixup' has no attribute 'report_below_element_captions'`).

- [ ] **Step 3: Implement `report_below_element_captions`**

Add to `tme_editor_app/src/fixup.py`:

```python
def report_below_element_captions(doc) -> list:
    """Return caption paragraphs that sit below their figure/table instead of above.

    APA 7 places the caption above the element; fixup flags any violation so
    the editor can fix it (manually, or via swap_captions_above).

    Returned entries look like:
        {"index": 12, "kind": "figure", "preview": "Figure 2. Student work…"}
    """
    reports = []
    body = doc.element.body
    # Iterate over body children in document order so we can see table vs paragraph neighbors.
    children = list(body.iterchildren())
    tag_p, tag_tbl = qn("w:p"), qn("w:tbl")

    para_idx = -1  # running index into doc.paragraphs for paragraph children only
    for i, el in enumerate(children):
        if el.tag != tag_p:
            continue
        para_idx += 1
        p = doc.paragraphs[para_idx]
        sn = p.style.name if p.style is not None else ""
        if sn not in ("TME Figure Caption", "TME Table Caption"):
            continue
        # Look at the previous non-empty sibling in body order.
        prev_el = None
        for back in range(i - 1, -1, -1):
            cand = children[back]
            if cand.tag == tag_p:
                # skip empty paragraph spacers
                if (cand.text or "").strip() == "" and cand.find(".//" + qn("w:t")) is None:
                    continue
                prev_el = cand
                break
            if cand.tag == tag_tbl:
                prev_el = cand
                break
        if prev_el is None:
            continue
        is_fig_caption = sn == "TME Figure Caption"
        is_tab_caption = sn == "TME Table Caption"
        prev_is_image_para = prev_el.tag == tag_p and (
            prev_el.find(".//" + qn("w:drawing")) is not None or
            prev_el.find(".//" + qn("w:pict")) is not None
        )
        prev_is_table = prev_el.tag == tag_tbl
        if is_fig_caption and prev_is_image_para:
            reports.append({
                "index": para_idx, "kind": "figure",
                "preview": (p.text[:80] or "").strip(),
            })
        elif is_tab_caption and prev_is_table:
            reports.append({
                "index": para_idx, "kind": "table",
                "preview": (p.text[:80] or "").strip(),
            })
    return reports
```

- [ ] **Step 4: Wire `report_below_element_captions` into `run_fixup`**

Change `run_fixup` to capture the report and add to the return dict. Near the end of `run_fixup`, after the existing stats are assembled:

```python
    below = report_below_element_captions(doc)

    doc.save(docx_path)

    fn_stats = fix_footnote_fonts(Path(docx_path))

    return {
        "block_quotes_remapped": bq_count,
        "refs_rescued": rescued_refs,
        "captions": caption_stats,
        "captions_below_element": below,
        "lists_cleared": list_n,
        "tables_centered": t_count,
        "masthead_ok": masthead_ok,
        "references_stripped": ref_stripped,
        "direct_formatting": direct_strip,
        "table_cells_normalized": cell_strip,
        "footnotes": fn_stats,
    }
```

(Note: the `"figures_glued"` key is already removed from Task 9.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest tme_editor_app/tests/test_fixup_captions.py -v`
Expected: all three tests PASS.

- [ ] **Step 6: Commit**

```bash
git add tme_editor_app/src/fixup.py tme_editor_app/tests/test_fixup_captions.py
git commit -m "$(cat <<'EOF'
Fixup: detect and report captions that sit below their figure/table

report_below_element_captions scans the document in body order and
returns {index, kind, preview} for every caption paragraph whose
immediately preceding block is an image paragraph (figure case) or a
w:tbl (table case). run_fixup now includes these in the stats dict as
"captions_below_element" so the Streamlit UI can show them.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Add `swap_captions_above` to fixup.py

**Files:**
- Modify: `tme_editor_app/src/fixup.py`
- Modify: `tme_editor_app/tests/test_fixup_captions.py`

- [ ] **Step 1: Add the failing test**

Append to `tme_editor_app/tests/test_fixup_captions.py`:

```python
def test_swap_captions_above_moves_figure_caption_up():
    doc = _make_doc_with_styles()
    _add_fake_drawing_paragraph(doc)
    doc.add_paragraph("Figure 1. Below.", style="TME Figure Caption")
    doc.add_paragraph("Some body paragraph.", style="TME Body")

    report = fixup.report_below_element_captions(doc)
    assert len(report) == 1

    moved = fixup.swap_captions_above(doc, report)
    assert moved == 1

    # After swap, caption should precede the drawing paragraph
    texts = [p.text for p in doc.paragraphs]
    # Find the figure caption and the drawing paragraph (the drawing paragraph
    # has empty text because _add_fake_drawing_paragraph created an empty one)
    cap_idx = next(i for i, t in enumerate(texts) if t.startswith("Figure 1"))
    # Drawing paragraph is the one right AFTER the caption now
    assert cap_idx < len(texts) - 1
    # Re-run report: should be empty now
    report2 = fixup.report_below_element_captions(doc)
    assert report2 == []


def test_swap_captions_above_moves_table_caption_up():
    doc = _make_doc_with_styles()
    doc.add_table(rows=2, cols=2)
    doc.add_paragraph("Table 1. Below.", style="TME Table Caption")

    report = fixup.report_below_element_captions(doc)
    assert len(report) == 1
    moved = fixup.swap_captions_above(doc, report)
    assert moved == 1
    assert fixup.report_below_element_captions(doc) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest tme_editor_app/tests/test_fixup_captions.py -v`
Expected: the two new tests FAIL (`AttributeError: module 'fixup' has no attribute 'swap_captions_above'`).

- [ ] **Step 3: Implement `swap_captions_above`**

Add to `tme_editor_app/src/fixup.py`:

```python
def swap_captions_above(doc, report: list) -> int:
    """Given entries from report_below_element_captions, move each caption
    paragraph to sit immediately before its figure/table.

    Operates at the XML element level. The caption paragraph's w:p element
    is detached from its current location and inserted just before the
    preceding w:p (image-bearing) or w:tbl element.

    Indices in the report are interpreted against the CURRENT document state,
    so callers should pass a freshly-generated report (do not cache across
    swaps). Returns the number of paragraphs actually moved.
    """
    moved = 0
    tag_p, tag_tbl = qn("w:p"), qn("w:tbl")
    for entry in report:
        # Re-resolve the caption paragraph each iteration since previous swaps
        # change paragraph indices. Match by the preview text to stay robust.
        preview = entry.get("preview", "")
        kind = entry["kind"]
        target_p = None
        for p in doc.paragraphs:
            if p.style is None:
                continue
            sn = p.style.name
            if kind == "figure" and sn != "TME Figure Caption":
                continue
            if kind == "table" and sn != "TME Table Caption":
                continue
            if p.text.strip().startswith(preview[:40].strip()):
                target_p = p
                break
        if target_p is None:
            continue

        cap_el = target_p._p
        parent = cap_el.getparent()
        # Find the preceding image paragraph or table
        prev = cap_el.getprevious()
        # Skip empty-paragraph spacers
        while prev is not None and prev.tag == tag_p:
            has_content = (
                prev.find(".//" + qn("w:t")) is not None or
                prev.find(".//" + qn("w:drawing")) is not None or
                prev.find(".//" + qn("w:pict")) is not None
            )
            if has_content:
                break
            prev = prev.getprevious()
        if prev is None:
            continue
        if kind == "figure" and prev.tag != tag_p:
            continue
        if kind == "table" and prev.tag != tag_tbl:
            continue

        parent.remove(cap_el)
        prev.addprevious(cap_el)
        moved += 1
    return moved
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest tme_editor_app/tests/test_fixup_captions.py -v`
Expected: all 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add tme_editor_app/src/fixup.py tme_editor_app/tests/test_fixup_captions.py
git commit -m "$(cat <<'EOF'
Fixup: add opt-in swap_captions_above to move below-element captions

Given a report list from report_below_element_captions, relocates each
caption's w:p element to sit just before its preceding image paragraph
or w:tbl. Designed to be invoked from the Streamlit UI behind a
checkbox; not called automatically by run_fixup.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: Migrate gray hex literals to palette constants across template source

**Files:**
- Modify: `template_build/src/tme_template/tagline.py`
- Modify: `template_build/src/tme_template/masthead.py`
- Modify: `template_build/src/tme_template/cover_page.py`
- Modify: `template_build/src/tme_template/cover_footer.py`
- Modify: `template_build/src/tme_template/headers_footers.py`
- Modify: `template_build/src/tme_template/front_matter.py`
- Modify: `template_build/src/tme_template/styles.py`

Strategy: one commit per file so each migration is reviewable on its own. Each file gets `from tme_template.colors import ...` imports added, and every `RGBColor(0xNN, 0xNN, 0xNN)` or raw hex string inline is replaced with the palette constant. The spec §6 migration table tells you the target for each value.

### 12a: tagline.py

- [ ] **Step 1:** Open `template_build/src/tme_template/tagline.py`. Replace the imports block:

```python
from tme_template.colors import LIGHT_PANEL_GRAY, META, UGA_RED
```

(Switch `TAGLINE_GRAY` → `META`; the deprecated alias is still present in `colors.py` but callers should reference `META` directly.)

- [ ] **Step 2:** In `_gray_run`, change the color line from `RGBColor(0x55, 0x55, 0x55)` to:

```python
    r.font.color.rgb = RGBColor.from_string(META)
```

Add `from docx.shared import RGBColor` if not already imported (it is).

- [ ] **Step 3:** Run all tests.

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests -v`
Expected: all pass.

- [ ] **Step 4:** Commit.

```bash
git add template_build/src/tme_template/tagline.py
git commit -m "$(cat <<'EOF'
tagline.py: use META palette constant (was #555)

Slightly lighter tagline italic per the deliberate 5-step grayscale.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### 12b: masthead.py

- [ ] **Step 1:** Open `template_build/src/tme_template/masthead.py`. No gray literals are present — masthead text is white on UGA red. The file imports `BLACK` and `UGA_RED` which both survive the palette change. Verify the import line:

```python
from tme_template.colors import BLACK, UGA_RED
```

- [ ] **Step 2:** No code change needed. Run tests to confirm:

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests -v`
Expected: all pass.

- [ ] **Step 3:** Skip commit — no file change. Move to 12c.

### 12c: cover_page.py

- [ ] **Step 1:** Add imports at top of `template_build/src/tme_template/cover_page.py`:

```python
from tme_template.colors import LINE, META, UGA_RED
```

(Update the existing import if it already pulls `UGA_RED` only.)

- [ ] **Step 2:** Replace color literals to match the palette:

| Location | Old | New |
|---|---|---|
| Affiliation superscript number | `RGBColor(0x55, 0x55, 0x55)` | `RGBColor.from_string(META)` |
| Affiliation text | `RGBColor(0x55, 0x55, 0x55)` | `RGBColor.from_string(META)` |
| Corresponding author line | `RGBColor(0x55, 0x55, 0x55)` | `RGBColor.from_string(META)` |
| Dates separator `·` | `RGBColor(0x99, 0x99, 0x99)` | `RGBColor.from_string(LINE)` |
| Dates label | `RGBColor(0x88, 0x88, 0x88)` | `RGBColor.from_string(META)` |
| Dates value | `RGBColor(0x66, 0x66, 0x66)` | `RGBColor.from_string(META)` |
| Rule 1 (`apply_bottom_rule`) | `hex_color="CCCCCC"` | `hex_color=LINE` |
| Rule 2 (`apply_bottom_rule`) | `hex_color="CCCCCC"` | `hex_color=LINE` |

- [ ] **Step 3:** Run tests.

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests -v`
Expected: all pass.

- [ ] **Step 4:** Commit.

```bash
git add template_build/src/tme_template/cover_page.py
git commit -m "$(cat <<'EOF'
cover_page.py: migrate grays to palette (META, LINE)

Affiliation, corresponding-author, and dates row now use META (#777)
instead of the ad-hoc #55/#66/#88 stack. Cover rules use LINE (#BBB)
instead of #CCC.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### 12d: cover_footer.py

- [ ] **Step 1:** Add import:

```python
from tme_template.colors import FOOTER_CREAM, TEXT_MUTED, UGA_RED
```

- [ ] **Step 2:** Replace `RGBColor(0x44, 0x44, 0x44)` (two occurrences) with `RGBColor.from_string(TEXT_MUTED)`.

- [ ] **Step 3:** Run tests + commit.

```bash
git add template_build/src/tme_template/cover_footer.py
git commit -m "$(cat <<'EOF'
cover_footer.py: use TEXT_MUTED constant (no visual change)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### 12e: headers_footers.py

- [ ] **Step 1:** Add import:

```python
from tme_template.colors import INK, LINE, META
```

- [ ] **Step 2:** In `_add_italic_gray_line`, change `RGBColor(0x44, 0x44, 0x44)` to `RGBColor.from_string(META)`.

(Running headers use #44 today — migrating to META #77 makes them slightly lighter, consistent with tagline italic. Note this is not in the spec migration table but follows the same META intent for italic metadata lines.)

- [ ] **Step 3:** In `_build_footer` (the one rewritten in Task 7), change the page-number `RGBColor(0x22, 0x22, 0x22)` to `RGBColor.from_string(INK)` and the `apply_top_rule(p, hex_color="EEEEEE", ...)` to `apply_top_rule(p, hex_color=LINE, ...)`.

- [ ] **Step 4:** Run tests.

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests -v`
Expected: all pass. The existing `test_footer_paragraph_is_centered` / `test_footer_contains_page_field` still pass; no test pins the specific hex, and that's intentional.

- [ ] **Step 5:** Commit.

```bash
git add template_build/src/tme_template/headers_footers.py
git commit -m "$(cat <<'EOF'
headers_footers.py: use INK/META/LINE palette constants

Running headers go to META (#777) from #444 for italic metadata
consistency; page number uses INK (#111); footer top rule uses LINE
(#BBB).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### 12f: front_matter.py

- [ ] **Step 1:** Add import:

```python
from tme_template.colors import INK, META, UGA_RED
```

- [ ] **Step 2:** Replace color literals per the spec table:

| Location | Old | New |
|---|---|---|
| Issue-cover vol/num red | `RGBColor(0xBA, 0x0C, 0x2F)` | (leave; already UGA red) |
| Issue-cover season italic | `RGBColor(0x44, 0x44, 0x44)` | `RGBColor.from_string(META)` |
| Issue-cover credit line | `RGBColor(0x77, 0x77, 0x77)` | `RGBColor.from_string(META)` |
| `_role_group` role label | `RGBColor(0x66, 0x66, 0x66)` | `RGBColor.from_string(META)` |
| `_role_group` name text | `RGBColor(0x11, 0x11, 0x11)` (implicit default) | leave |
| `_role_group_in_cell` role label | `RGBColor(0x66, 0x66, 0x66)` | `RGBColor.from_string(META)` |
| Formal title wordmark | `RGBColor(0x11, 0x11, 0x11)` | `RGBColor.from_string(INK)` |
| Formal title "OK" italic | `RGBColor(0x55, 0x55, 0x55)` | `RGBColor.from_string(META)` |
| Formal title season | `RGBColor(0x44, 0x44, 0x44)` | `RGBColor.from_string(META)` |

- [ ] **Step 3:** Run tests + commit.

```bash
git add template_build/src/tme_template/front_matter.py
git commit -m "$(cat <<'EOF'
front_matter.py: migrate grays to palette constants

Season / credit / role / formal-title metadata all collapse onto META
(#777). Wordmark uses INK (#111). No visual change greater than one
palette step in any location.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### 12g: styles.py

- [ ] **Step 1:** Add import at the top:

```python
from tme_template.colors import BLOCKQUOTE_INK, INK, TEXT_MUTED
```

- [ ] **Step 2:** Replace color literals:

| Style | Old | New |
|---|---|---|
| TME Title | `RGBColor(0x11, 0x11, 0x11)` | `RGBColor.from_string(INK)` |
| TME H1 | `RGBColor(0x11, 0x11, 0x11)` | `RGBColor.from_string(INK)` |
| TME H2 | `RGBColor(0x22, 0x22, 0x22)` | `RGBColor.from_string(INK)` |
| TME H3 | `RGBColor(0x33, 0x33, 0x33)` | `RGBColor.from_string(INK)` |
| TME Figure Caption | `RGBColor(0x44, 0x44, 0x44)` | `RGBColor.from_string(TEXT_MUTED)` |
| TME Table Caption | `RGBColor(0x44, 0x44, 0x44)` | `RGBColor.from_string(TEXT_MUTED)` |
| TME Footnote | `RGBColor(0x44, 0x44, 0x44)` | `RGBColor.from_string(TEXT_MUTED)` |
| TME Pullquote | `RGBColor(0x1A, 0x1A, 0x1A)` | `RGBColor.from_string(INK)` |
| TME Block Quote | `RGBColor(0x33, 0x33, 0x33)` | `RGBColor.from_string(BLOCKQUOTE_INK)` |

- [ ] **Step 3:** Run tests.

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests -v`
Expected: all pass.

- [ ] **Step 4:** Commit.

```bash
git add template_build/src/tme_template/styles.py
git commit -m "$(cat <<'EOF'
styles.py: migrate paragraph-style colors to palette constants

Every TME paragraph style now resolves its font color through the
palette. Title/H1/H2/H3/Pullquote → INK. Captions + Footnote →
TEXT_MUTED. Block Quote → BLOCKQUOTE_INK.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

### 12h: Remove deprecation aliases

- [ ] **Step 1:** Confirm no remaining references to deprecated names.

```bash
cd /Users/jenniferkleiman/Documents/tme-editor
grep -rn "TAGLINE_GRAY\|RULE_GRAY" template_build/src tme_editor_app/src || echo "clean"
```

Expected: `clean`. If anything prints, finish migrating those references before continuing.

- [ ] **Step 2:** Update `test_colors.py` — replace the alias test with a "removed" assertion:

In `template_build/tests/test_colors.py`, delete `test_deprecation_aliases_resolve_to_new_palette` and add:

```python
def test_removed_constants_are_gone():
    assert not hasattr(colors, "TAGLINE_GRAY")
    assert not hasattr(colors, "RULE_GRAY")
```

- [ ] **Step 3:** Run the test to verify it fails (the aliases are still present).

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests/test_colors.py -v`
Expected: `test_removed_constants_are_gone` FAILS.

- [ ] **Step 4:** Remove the deprecation block from `colors.py`.

In `template_build/src/tme_template/colors.py`, delete this block:

```python
# ---------- Deprecated aliases (remove after Task 12 migration completes) ----------
# Kept so existing callers continue to import successfully during the refactor.
# Task 12h removes these and flips the test to assert they are gone.
TAGLINE_GRAY = META   # deprecated — callers migrate to META
RULE_GRAY = LINE      # deprecated — callers migrate to LINE
```

- [ ] **Step 5:** Run all tests to verify they pass.

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && python -m pytest template_build/tests tme_editor_app/tests -v`
Expected: every test passes, including the new `test_removed_constants_are_gone`.

- [ ] **Step 6:** Commit.

```bash
git add template_build/src/tme_template/colors.py template_build/tests/test_colors.py
git commit -m "$(cat <<'EOF'
colors.py: remove deprecated TAGLINE_GRAY / RULE_GRAY aliases

All callers now use the 5-step palette constants directly. The alias
shim was a migration scaffold; it's served its purpose.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: Wire caption reports + opt-in swap into the Streamlit app

**Files:**
- Modify: `tme_editor_app/app.py:230-260`

- [ ] **Step 1: Add a checkbox above the Finalize button**

In `app.py`, inside the `populated is not None` block, add a checkbox before the Finalize button:

```python
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
                ...
```

- [ ] **Step 2: After `fixup_stats = run_fixup(...)`, surface the report**

Replace the block that currently reads:

```python
                        st.session_state.proof_bytes = proof_path.read_bytes()
                        st.session_state.proof_filename = _proof_filename(meta)

                        st.success("Proof finalized.")
                        with st.expander("Style + fixup stats"):
                            st.markdown("**apply_styles:**")
                            st.json(style_stats)
                            st.markdown("**fixup:**")
                            st.json(fixup_stats)
```

with:

```python
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
```

- [ ] **Step 3: Manual smoke test**

Run: `cd /Users/jenniferkleiman/Documents/tme-editor && GEMINI_API_KEY=dummy streamlit run tme_editor_app/app.py` in a terminal.

In a browser at `http://localhost:8501`:

1. Upload the Moore manuscript (`/Users/jenniferkleiman/Documents/tme/1-VV.I_Cover, Note, & TOC TEMPLATE (1).docx` or any docx with figures).
2. For offline testing without hitting Gemini, cancel extraction and use the Phase-2 path directly with an existing populated file (load `/Users/jenniferkleiman/Documents/tme/TME_Moore_2026_starter.pre-fixup.docx` as the "populated starter").
3. Click Finalize without the checkbox. Expect: if any figure captions are below their figures in that file, a yellow warning lists them. If none, no warning.
4. Click Finalize again with the checkbox on. Expect: blue info message reporting how many were moved.

Stop the server when done.

- [ ] **Step 4: Commit**

```bash
git add tme_editor_app/app.py
git commit -m "$(cat <<'EOF'
App: surface below-element caption warnings + opt-in auto-swap

Phase 2 now displays a yellow warning listing any caption paragraphs
that sit below their figure/table (APA 7 puts captions above). An
opt-in checkbox asks fixup to relocate them after the normal battery
runs; off by default so the editor remains in control.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: Rebuild TME_Template_2026.docx from updated source

**Files:**
- Modify (regenerate): `TME_Template_2026.docx`

- [ ] **Step 1: Install the packages in a clean venv (skip if already done)**

Run from repo root:

```bash
cd /Users/jenniferkleiman/Documents/tme-editor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 2: Run the template builder**

```bash
cd /Users/jenniferkleiman/Documents/tme-editor
python template_build/src/build_template.py
```

Expected: prints `Wrote /Users/jenniferkleiman/Documents/tme-editor/TME_Template_2026.docx`. Non-zero exit is a bug — read the traceback and fix the offending file before continuing.

- [ ] **Step 3: Visual QA in Word**

Open the generated `TME_Template_2026.docx` and verify:

- Cover sample page (page 4): title has visible breathing room below the gray tagline strip.
- ABOUT THE AUTHORS label appears **above** ABSTRACT on the sample cover.
- Body page: footer shows only a centered page number — no `© 2026 The Authors` or `CC BY 4.0` string.
- H3 in body sample section reads bold, not italic. (If the sample doesn't include an H3, add one to `build_template.py` temporarily under the body heading, rebuild, then revert that line before committing.)

- [ ] **Step 4: Commit the regenerated template**

```bash
cd /Users/jenniferkleiman/Documents/tme-editor
# Check .gitignore — *.docx is currently ignored; the top-level template is
# the one .docx we do want committed. Force-add it:
git add -f TME_Template_2026.docx
git commit -m "$(cat <<'EOF'
Regenerate TME_Template_2026.docx from updated source

Picks up: title breathing room, cover reorder (About Authors above
Abstract), simplified body footer, APA-7 caption styles, 5-step
palette, H3 bold.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

If Git complains that the file is ignored, add an explicit allow-list entry to `.gitignore` immediately above the line `*.docx`:

```
!TME_Template_2026.docx
```

Then `git add .gitignore TME_Template_2026.docx` and commit together with the message above.

---

## Task 15: Rerun Moore pipeline to regenerate the proof

**Files:**
- Modify (outside repo): `/Users/jenniferkleiman/Documents/tme/TME_Moore_2026_starter.docx`, `TME_Moore_2026_proof.pdf`

This task runs *against* the `tme/` scratch tree so Jennifer's local proof is refreshed. The code lives in `tme-editor/`; the inputs live in `tme/`.

- [ ] **Step 1: Mirror tme-editor source into tme**

From repo root:

```bash
cd /Users/jenniferkleiman/Documents
rsync -av --exclude='.git' --exclude='.venv' --exclude='__pycache__' \
  --exclude='.superpowers' --exclude='docs/superpowers' \
  tme-editor/template_build/src/ tme/template_build/src/
rsync -av --exclude='.git' --exclude='.venv' --exclude='__pycache__' \
  tme-editor/tme_editor_app/src/ tme/tme_editor_app/src/
cp tme-editor/tme_editor_app/app.py tme/tme_editor_app/app.py
```

- [ ] **Step 2: Run fixup against the Moore paste-state backup**

```bash
cd /Users/jenniferkleiman/Documents/tme
cp "TME_Moore_2026_starter.pre-fixup.docx" "TME_Moore_2026_starter.docx"
source ../tme-editor/.venv/bin/activate 2>/dev/null || true
python -c "
import sys
sys.path.insert(0, 'tme_editor_app/src')
sys.path.insert(0, 'template_build/src')
sys.path.insert(0, 'moore_build/src')
from apply_styles import apply_styles
from fixup import run_fixup
# Use a minimal ArticleMeta-shaped object — apply_styles only reads title/authors/abstract/keywords for dedup
class A: pass
meta = A()
meta.title = 'Mathematical Modeling in a Secondary Classroom'
meta.authors = [type('X', (), {'name': 'Kevin C. Moore'})()]
meta.abstract = ''
meta.keywords = []
meta.affiliations = []
path = 'TME_Moore_2026_starter.docx'
s = apply_styles(path, meta)
print('apply_styles:', s)
f = run_fixup(path)
print('fixup:', f)
"
```

Expected: prints two dicts. `fixup`'s dict includes `captions_below_element` as a list.

- [ ] **Step 2b: Visually QA the resulting starter.docx**

Open `TME_Moore_2026_starter.docx` in Word. Verify all seven changes show up on the cover and body pages.

- [ ] **Step 3: Export the Moore proof PDF**

In Word: File → Save As → PDF. Save as `TME_Moore_2026_proof.pdf` in the `tme/` dir, overwriting the previous proof. Visually compare to `TME_Moore_2026.docx` (the earlier reference) to catch regressions.

- [ ] **Step 4: No commit here**

The `tme/` tree is local scratch (per the spec). Nothing is pushed.

---

## Self-review

### Spec coverage

- Change 1 (title space_before) → Task 3. ✓
- Change 2 (cover reorder) → Task 6. ✓
- Change 3 (body footer simplification) → Tasks 7, 8. ✓
- Change 4 (caption styles + report + swap) → Tasks 5, 9, 10, 11, 13. ✓
- Change 5 (font policy no-change) → documented in spec, nothing to do. ✓
- Change 6 (5-step palette + migration + alias removal) → Tasks 2, 12a–12h. ✓
- Change 7 (H3 bold) → Task 4. ✓
- Rebuild `TME_Template_2026.docx` → Task 14. ✓
- Rerun Moore pipeline → Task 15. ✓

### Type consistency

- `set_running_footer` is called with `section=…` (kwarg) in `article_starter.py` and `build_template.py` after Task 8; the new signature in Task 7 accepts `section=None` as a kwarg. Matches.
- `report_below_element_captions` returns `list[dict]` with keys `index/kind/preview`. `swap_captions_above` reads `preview` and `kind`. The Streamlit app reads `kind` and `preview`. Consistent.
- `run_fixup` return dict adds `captions_below_element` (list) and drops `figures_glued` (int). App code in Task 13 reads `fixup_stats.get("captions_below_element", [])` with a safe default — robust to stats key evolution.

### No placeholders

Every code block is concrete. Every `git commit` includes a full message. Every test has its full body. No "TBD" / "similar to Task N" / "add error handling."
