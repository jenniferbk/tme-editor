# Editor App Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix every editor-app finding from the 7 Oct 2026 code review (A2–A15, the app nits, Dockerfile/README drift, the dead smoke test) and add the end-to-end test the review asked for.

**Architecture:** `tme_editor_app/src/` holds the pipeline as small modules (extractor → article_starter → apply_styles → fixup) and `app.py` is a thin Streamlit UI over them. Each task fixes one module group with tests first. UI logic that needs testing moves into `src/` helpers; the UI itself gets a Streamlit `AppTest` smoke test. Metadata travels inside the starter .docx so Phase 2 survives a lost browser session.

**Tech Stack:** Python 3.11+, Streamlit 1.56, python-docx 1.2.0, google-genai 1.63 (pydantic 2 comes with it), Pillow 12, pytest. Run tests with the Homebrew `python3` from `tme_editor_app/`.

**Spec:** `docs/code-review-2026-10-07.md` (findings prefixed A, the first nits list, and the Tests section).

## Global Constraints

- Edit only: `tme_editor_app/**`, `requirements.txt`, `README.md` (repo root). Another plan edits `template_build/**` concurrently; do not touch it. `moore_build/**` is left in place untouched (legacy), only de-referenced.
- `template_build/src/tme_template/layout.py` exists and exports `MASTHEAD_LEFT_WIDTH`, `MASTHEAD_RIGHT_WIDTH`, `FULL_BLEED_WIDTH` (python-docx `Length`; use `.twips`), `PAGE_WIDTH_IN`, `BLEED_IN`, `MASTHEAD_LOGO_FRACTION`.
- The paragraph style `"TME Table Text"` may or may not exist in an uploaded document; `fixup.update_styles` must create it when missing (Georgia 10pt, line spacing 1.0, 0pt before, 2pt after), exactly as it already does for `TME Block Quote`.
- Keep these stats keys, which `app.py` reads: `style_stats["classifier"]` (string, `"gemini"` on success), `fixup_stats["captions_below_element"]`.
- No test may call Gemini or the network. Monkeypatch `classifier.classify_paragraphs_with_report` (new in Task 4) or the parsing helpers.
- Dependency floors in `requirements.txt`: `google-genai>=1.0`, keep `opencv-python-headless>=4.10,<5`, keep `python-docx>=1.1`.
- Run `cd tme_editor_app && python3 -m pytest tests -q` after every task; it must stay green.
- Commit after each task. Imperative subject under 70 characters; end the message with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

## Review Focus

Inputs the spec implies but no finding spells out. Each has a test in the task named.

1. A plain document with no section breaks at all (not a starter) must classify every paragraph instead of none. Test in Task 3.
2. Metadata JSON written by a future starter with extra keys must still load; unknown keys are dropped, not fatal. Test in Task 6.
3. A reference paragraph whose only run is inside a hyperlink must still lose its pasted font. Test in Task 2.
4. A content table with one row must not be marked as having a repeating header. Test in Task 5.
5. A Gemini reply with duplicate indices must count as one label per paragraph and report nothing missing. Test in Task 4.

---

### Task 1: Stop depending on the Moore package

**Files:**
- Create: `tme_editor_app/src/endnote.py` (copy of `moore_build/src/moore_pipeline/endnote.py`, unchanged content)
- Modify: `tme_editor_app/src/pipeline.py:9`
- Modify: `tme_editor_app/app.py:27-34`
- Modify: `tme_editor_app/tests/conftest.py`
- Delete: `tme_editor_app/test_pipeline.py` (collects no tests; fixtures are gitignored)
- Modify: `requirements.txt` (drop `-e ./moore_build`; `google-genai>=1.0`)
- Modify: `tme_editor_app/Dockerfile`
- Modify: `README.md` (repo root) and `tme_editor_app/README.md`
- Test: `tme_editor_app/tests/test_endnote_module.py` (new)

**Interfaces:**
- Produces: `endnote.resolve_endnote_citations(src_docx: str, dst_docx: str)` importable from `tme_editor_app/src`.

- [ ] **Step 1: Write the failing test**

```python
"""The EndNote resolver lives in the app now; a plain document passes through."""
from docx import Document


def test_resolver_is_importable_and_copies_a_plain_document(tmp_path):
    from endnote import resolve_endnote_citations

    src = tmp_path / "in.docx"
    dst = tmp_path / "out.docx"
    doc = Document()
    doc.add_paragraph("No EndNote fields here.")
    doc.save(src)

    resolve_endnote_citations(str(src), str(dst))

    assert dst.exists()
    assert [p.text for p in Document(dst).paragraphs] == ["No EndNote fields here."]
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tme_editor_app && python3 -m pytest tests/test_endnote_module.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'endnote'`.

- [ ] **Step 3: Move the module and cut the references**

```bash
cp moore_build/src/moore_pipeline/endnote.py tme_editor_app/src/endnote.py
```

`pipeline.py:9`: `from endnote import resolve_endnote_citations`.

`app.py:27-34`: remove `_TME / 'moore_build' / 'src'` from the tuple.

`tests/conftest.py`: remove `REPO / "moore_build" / "src"` from the tuple.

`git rm tme_editor_app/test_pipeline.py`.

`requirements.txt`: delete the `-e ./moore_build` line; change `google-genai>=0.7` to `google-genai>=1.0  # response_schema and thinking_config need the 1.x SDK`.

`tme_editor_app/Dockerfile`: replace the COPY/RUN block with

```dockerfile
# Copy the shared layout package, the app, the logo assets and the root
# requirements (which installs template_build as an editable path).
COPY requirements.txt /app/requirements.txt
COPY template_build /app/template_build
COPY tme_editor_app /app/tme_editor_app
COPY assets /app/assets

RUN pip install --no-cache-dir -r /app/requirements.txt
```
Check `grep -n "LOGO_H\|assets" tme_editor_app/src/article_starter.py` and confirm the logo path resolves under `/app/assets` (it is computed relative to the repo root; the COPY above provides it).

Root `README.md`: in "Repo layout" replace the `moore_build/` bullet with
`- \`moore_build/\` — legacy one-off scripts for the Spring 2026 Moore article. Not used by the app (the EndNote resolver now lives in \`tme_editor_app/src/endnote.py\`).`

`tme_editor_app/README.md`: in "Running locally" replace the pip lines with `pip install -r ../requirements.txt` (one line, run from `tme_editor_app/`), delete `pip install -e ../template_build -e ../moore_build`; in "What it does" step 6 replace "run the companion styling script, export to PDF" with "come back to the app's Phase 2, upload the pasted file, click **Finalize**, then export the proof to PDF"; in "Codebase layout" add `apply_styles.py`, `classifier.py`, `fixup.py`, `endnote.py`, `session_meta.py` lines (the last is created in Task 6).

- [ ] **Step 4: Run the suite**

Run: `cd tme_editor_app && python3 -m pytest tests -q`
Expected: all pass (the new test included).

- [ ] **Step 5: Commit**

```bash
git add tme_editor_app/src/endnote.py tme_editor_app/src/pipeline.py tme_editor_app/app.py tme_editor_app/tests/conftest.py tme_editor_app/tests/test_endnote_module.py requirements.txt tme_editor_app/Dockerfile README.md tme_editor_app/README.md
git rm -q tme_editor_app/test_pipeline.py
git commit -m "app: own the EndNote resolver; drop moore_build from install, Dockerfile and docs"
```

---

### Task 2: Run-level fixes in fixup — hyperlink runs, table text, footnote fonts, dead strip

**Files:**
- Modify: `tme_editor_app/src/fixup.py`
- Test: `tme_editor_app/tests/test_fixup_runs.py` (new)

**Interfaces:**
- Produces: `fixup._iter_runs(paragraph) -> list[docx.text.run.Run]` (every `w:r` under the paragraph, including inside `w:hyperlink` and `w:ins`).
- Produces: `fixup.rewrite_footnote_xml(xml: str) -> tuple[str, dict]` (pure; `fix_footnote_fonts` calls it).
- Removes: `strip_reference_run_formatting` and the `"references_stripped"` stats key.
- `normalize_table_cells(doc, skip_indices=None)` now also assigns `"TME Table Text"` to every cell paragraph of a content table (skip handling is finished in Task 3; for now keep the `(0, 1)` default).

- [ ] **Step 1: Write the failing tests**

```python
"""Run-level stripping reaches hyperlinks; tables get a TME style; footnote
font rewrite leaves symbol fonts alone; the redundant reference strip is gone."""
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

import fixup
from tme_template.styles import (
    register_body_style, register_title_style,
    register_heading_styles, register_remaining_styles,
)

HYPERLINK_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"


def _doc():
    doc = Document()
    for f in (register_body_style, register_title_style, register_heading_styles, register_remaining_styles):
        f(doc)
    return doc


def _add_hyperlink_run(p, text, font="Times New Roman"):
    r_id = p.part.relate_to("https://doi.org/10.1/x", HYPERLINK_REL, is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), r_id)
    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), font)
    rPr.append(fonts)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "24")
    rPr.append(sz)
    r.append(rPr)
    t = OxmlElement("w:t")
    t.text = text
    r.append(t)
    h.append(r)
    p._p.append(h)
    return r


def test_strip_direct_formatting_reaches_runs_inside_hyperlinks():
    doc = _doc()
    p = doc.add_paragraph("Smith, J. (2020). Title. ", style="TME Reference")
    r = _add_hyperlink_run(p, "https://doi.org/10.1/x")

    fixup.strip_direct_formatting(doc)

    rPr = r.find(qn("w:rPr"))
    assert rPr.find(qn("w:rFonts")) is None and rPr.find(qn("w:sz")) is None


def test_reference_with_only_a_hyperlink_run_is_still_stripped():
    doc = _doc()
    p = doc.add_paragraph(style="TME Reference")
    r = _add_hyperlink_run(p, "https://doi.org/10.1/x")
    fixup.strip_direct_formatting(doc)
    assert r.find(qn("w:rPr")).find(qn("w:rFonts")) is None


def test_redundant_reference_strip_is_gone():
    assert not hasattr(fixup, "strip_reference_run_formatting")


def test_content_table_cells_get_table_text_style():
    doc = _doc()
    t = doc.add_table(rows=1, cols=1)
    cell_p = t.cell(0, 0).paragraphs[0]
    cell_p.add_run("x").font.name = "Times New Roman"

    fixup.update_styles(doc)              # creates TME Table Text if missing
    fixup.normalize_table_cells(doc, skip_indices=())

    assert cell_p.style.name == "TME Table Text"
    assert doc.styles["TME Table Text"].font.name == "Georgia"


def test_footnote_rewrite_keeps_symbol_fonts():
    xml = ('<w:footnotes xmlns:w="x"><w:r><w:rPr><w:rFonts w:ascii="Times New Roman"/>'
           '<w:sz w:val="20"/></w:rPr></w:r><w:r><w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol"/>'
           '</w:rPr></w:r><w:r><w:rPr><w:rFonts w:ascii="Cambria Math"/></w:rPr></w:r></w:footnotes>')
    out, stats = fixup.rewrite_footnote_xml(xml)
    assert 'w:ascii="Georgia"' in out
    assert 'w:ascii="Symbol"' in out and 'w:ascii="Cambria Math"' in out
    assert stats["rfonts_rewritten"] == 1 and stats["sz_stripped"] == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tme_editor_app && python3 -m pytest tests/test_fixup_runs.py -q`
Expected: 5 FAIL (hyperlink runs untouched; function still exists; cells keep source style; `rewrite_footnote_xml` missing).

- [ ] **Step 3: Implement**

In `fixup.py`:

Add near the top of the content-remapping section:

```python
def _iter_runs(p) -> list:
    """Every run in the paragraph, including runs inside w:hyperlink and
    w:ins. Paragraph.runs returns only direct w:r children, which is how a
    hyperlinked DOI kept Times New Roman while the rest went Georgia."""
    from docx.text.run import Run
    return [Run(r, p) for r in p._p.iter(qn("w:r"))]
```

In `strip_direct_formatting`, replace `for r in p.runs:` with `for r in _iter_runs(p):`.

Delete `strip_reference_run_formatting` entirely; in `run_fixup` delete `ref_stripped = strip_reference_run_formatting(doc)` and the `"references_stripped": ref_stripped,` line.

In `update_styles`, after the `TME Block Quote` block add:

```python
    if "TME Table Text" in style_names:
        tt = styles["TME Table Text"]
    else:
        tt = styles.add_style("TME Table Text", WD_STYLE_TYPE.PARAGRAPH)
    tt.font.name = "Georgia"
    tt.font.size = Pt(10)
    tt.paragraph_format.line_spacing = 1.0
    tt.paragraph_format.space_before = Pt(0)
    tt.paragraph_format.space_after = Pt(2)
```

Rewrite `normalize_table_cells`:

```python
def normalize_table_cells(doc, skip_indices=(0, 1)) -> int:
    """For content tables (not the cover tables), put every cell paragraph in
    TME Table Text and strip run-level font name and size overrides, so
    pasted tables render in Georgia rather than the theme font. Bold and
    italic are kept; they carry meaning in tables. Returns the number of
    run elements stripped."""
    tt = doc.styles["TME Table Text"]
    n = 0
    for i, table in enumerate(doc.tables):
        if i in skip_indices:
            continue
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.style = tt
                    for r in _iter_runs(p):
                        rPr = r._r.find(qn("w:rPr"))
                        if rPr is None:
                            continue
                        for tag in ("w:rFonts", "w:sz", "w:szCs"):
                            for el in rPr.findall(qn(tag)):
                                rPr.remove(el)
                                n += 1
    return n
```

Split `fix_footnote_fonts` into a pure rewrite plus the zip step:

```python
# Fonts whose glyphs are not letters; rewriting them to Georgia changes the
# symbol shown (Symbol-font bullets, math operators, Wingdings marks).
_KEEP_FONTS_RE = re.compile(r'w:(ascii|hAnsi)="(Symbol|Cambria Math|Wingdings\w*|MT Extra|Webdings)"')


def rewrite_footnote_xml(xml: str) -> tuple[str, dict]:
    """Normalize footnotes.xml text: every ordinary rFonts becomes Georgia,
    explicit sizes are removed so the Footnote Text style's size applies, and
    runs with no rFonts get one. Symbol fonts are left alone."""
    rewritten = 0

    def _rewrite_rfonts(m):
        nonlocal rewritten
        if _KEEP_FONTS_RE.search(m.group(0)):
            return m.group(0)
        rewritten += 1
        return '<w:rFonts w:ascii="Georgia" w:hAnsi="Georgia" w:cs="Georgia"/>'
    xml = re.sub(r"<w:rFonts\b[^/]*/>", _rewrite_rfonts, xml)

    stripped = 0
    for pattern in (r"<w:sz\b[^/]*/>", r"<w:szCs\b[^/]*/>"):
        xml, n = re.subn(pattern, "", xml)
        stripped += n

    injected = 0

    def _inject_rfonts(m):
        nonlocal injected
        inner = m.group(1)
        if "<w:rFonts" in inner:
            return m.group(0)
        injected += 1
        return f'<w:rPr>{inner}<w:rFonts w:ascii="Georgia" w:hAnsi="Georgia" w:cs="Georgia"/></w:rPr>'
    xml = re.sub(r"<w:rPr>(.*?)</w:rPr>", _inject_rfonts, xml, flags=re.DOTALL)
    return xml, {"rfonts_rewritten": rewritten, "rfonts_injected": injected, "sz_stripped": stripped}


def fix_footnote_fonts(docx_path: Path) -> dict:
    src = str(docx_path)
    with zipfile.ZipFile(src, "r") as z:
        if "word/footnotes.xml" not in z.namelist():
            return {"rfonts_rewritten": 0, "rfonts_injected": 0, "sz_stripped": 0}
        xml = z.read("word/footnotes.xml").decode("utf-8")
    xml, stats = rewrite_footnote_xml(xml)
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".docx")
    os.close(tmp_fd)
    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/footnotes.xml":
                data = xml.encode("utf-8")
            zout.writestr(item, data)
    shutil.move(tmp_path, src)
    return stats
```

Update the module docstring bullet `- reference run format strip` to `- run-level font/size strip on structural styles (reaches hyperlink runs)` and add `- content-table cells → TME Table Text`.

- [ ] **Step 4: Run the suite**

Run: `cd tme_editor_app && python3 -m pytest tests -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add tme_editor_app/src/fixup.py tme_editor_app/tests/test_fixup_runs.py
git commit -m "fixup: strip hyperlink runs, style table cells, keep symbol fonts, drop redundant strip"
```

---

### Task 3: Find the body and the cover tables by structure

**Files:**
- Modify: `tme_editor_app/src/apply_styles.py` (`find_body_start_index`, header restore loop)
- Modify: `tme_editor_app/src/fixup.py` (`cover_table_count`, `fix_content_tables`, `normalize_table_cells` defaults, `fix_masthead_grid` constants)
- Test: `tme_editor_app/tests/test_structure_detection.py` (new)

**Interfaces:**
- Produces: `apply_styles.STARTER_COVER_SECTION_BREAKS = 2` and `apply_styles.find_body_start_index(paragraphs) -> int | None` (index after the SECOND paragraph-embedded `w:sectPr`; after the last one if fewer exist; None if none).
- Produces: `fixup.cover_table_count(doc) -> int` (tables that precede the body start).
- `fix_content_tables(doc, skip_indices=None)` and `normalize_table_cells(doc, skip_indices=None)`: `None` means `range(cover_table_count(doc))`.

- [ ] **Step 1: Write the failing tests**

```python
"""Body start and cover tables are found by the starter's structure, not by
'last section break' or hard-coded table indices."""
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn

import apply_styles
import fixup
from article_starter import build_article_starter
from extractor import ArticleMeta, AuthorMeta


def _starter(tmp_path):
    out = tmp_path / "starter.docx"
    meta = ArticleMeta(title="A Title", authors=[AuthorMeta(name="Ada Lovelace", bio="b")],
                       affiliations=["UGA"], abstract="abs", keywords=["k"])
    build_article_starter(meta=meta, headshots={}, out_path=out)
    return out


def test_body_starts_at_the_placeholder_even_after_a_pasted_section_break(tmp_path):
    doc = Document(_starter(tmp_path))
    paras = list(doc.paragraphs)
    start = apply_styles.find_body_start_index(paras)
    assert paras[start].text.startswith("[Paste")

    doc.add_paragraph("Body text.")
    doc.add_section(WD_SECTION.NEW_PAGE)      # a landscape section pasted by the editor
    doc.add_paragraph("Wide table lives here.")
    paras = list(doc.paragraphs)
    assert apply_styles.find_body_start_index(paras) == start


def test_plain_document_without_breaks_classifies_everything():
    doc = Document()
    doc.add_paragraph("a")
    assert apply_styles.find_body_start_index(list(doc.paragraphs)) is None


def test_cover_tables_are_counted_by_position(tmp_path):
    doc = Document(_starter(tmp_path))
    assert fixup.cover_table_count(doc) == 3      # masthead, tagline, author card
    doc.add_table(rows=2, cols=2)                 # pasted content table
    assert fixup.cover_table_count(doc) == 3


def test_fix_content_tables_leaves_the_author_card_alone(tmp_path):
    doc = Document(_starter(tmp_path))
    card = doc.tables[2]
    before = card._tbl.xml
    pasted = doc.add_table(rows=2, cols=2)
    pasted.cell(0, 0).text = "h"

    n = fixup.fix_content_tables(doc)

    assert n == 1
    assert card._tbl.xml == before
    assert pasted._tbl.tblPr.find(qn("w:jc")).get(qn("w:val")) == "center"


def test_masthead_grid_uses_layout_constants(tmp_path):
    from tme_template.layout import MASTHEAD_LEFT_WIDTH, MASTHEAD_RIGHT_WIDTH
    doc = Document(_starter(tmp_path))
    fixup.fix_masthead_grid(doc)
    cols = [int(c.get(qn("w:w"))) for c in doc.tables[0]._tbl.tblGrid.findall(qn("w:gridCol"))]
    assert cols == [MASTHEAD_LEFT_WIDTH.twips, MASTHEAD_RIGHT_WIDTH.twips]
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tme_editor_app && python3 -m pytest tests/test_structure_detection.py -q`
Expected: FAIL on the pasted-break case, on `cover_table_count` missing, and on the author card being modified.

- [ ] **Step 3: apply_styles.py**

Replace `find_body_start_index` with:

```python
# The starter embeds exactly two section breaks before the body: masthead →
# cover (continuous) and cover → body (next page). Anything the editor pastes
# after that (a landscape section for a wide table) adds more, so count from
# the front rather than taking the last one.
STARTER_COVER_SECTION_BREAKS = 2


def _has_embedded_sectpr(p) -> bool:
    pPr = p._p.find(qn("w:pPr"))
    return pPr is not None and pPr.find(qn("w:sectPr")) is not None


def find_body_start_index(paragraphs) -> Optional[int]:
    """Index of the first body paragraph, or None when the document has no
    paragraph-embedded section break at all (a plain document: everything
    is body)."""
    breaks = [i for i, p in enumerate(paragraphs) if _has_embedded_sectpr(p)]
    if not breaks:
        return None
    k = min(STARTER_COVER_SECTION_BREAKS, len(breaks)) - 1
    return breaks[k] + 1
```

Change the header-restore block so every body section is covered:

```python
    try:
        from tme_template.headers_footers import set_running_footer, set_running_headers
        cite = author_cite_text(meta)
        short_title = meta.title if len(meta.title) < 60 else meta.title[:57] + "..."
        for body_section in doc.sections[STARTER_COVER_SECTION_BREAKS:]:
            set_running_headers(doc, author_cite=cite, short_title=short_title, section=body_section)
            set_running_footer(doc, section=body_section)
        stats["footer_restored"] = True
    except Exception as e:
        stats["footer_restored"] = f"failed: {e}"
```
with `from article_starter import author_cite_text` at the top (Task 6 adds that function; until then define it in `article_starter.py` now as part of this task):

```python
def author_cite_text(meta) -> str:
    """Running-head author form: 'Moore', 'Moore & Yasuda', 'Moore et al.'"""
    lasts = [a.name.rsplit(" ", 1)[-1] for a in (meta.authors or []) if a.name]
    if not lasts:
        return "Author"
    if len(lasts) == 1:
        return lasts[0]
    if len(lasts) == 2:
        return f"{lasts[0]} & {lasts[1]}"
    return f"{lasts[0]} et al."
```
and in `build_article_starter` replace the inline `cite_last_names = " & ".join(...)` with `author_cite=author_cite_text(meta)`.

- [ ] **Step 4: fixup.py**

Add after `_body_paragraphs`:

```python
def cover_table_count(doc) -> int:
    """Number of tables that precede the article body (masthead, tagline and
    author card in a fresh starter; two if Word merged the first pair). Skip
    these by position rather than by hard-coded index."""
    paras = list(doc.paragraphs)
    start = find_body_start_index(paras)
    if start is None:
        return 0
    start_el = paras[start]._p if start < len(paras) else None
    n = 0
    for el in doc.element.body.iterchildren():
        if el is start_el:
            break
        if el.tag == qn("w:tbl"):
            n += 1
    return n
```

`fix_content_tables(doc, skip_indices=None)`: first line `if skip_indices is None: skip_indices = range(cover_table_count(doc))`; same in `normalize_table_cells`. Update both docstrings to say so.

`fix_masthead_grid`: replace

```python
    BLEED = 90  # twips
    COL0, COL1 = 4651, 7589 + BLEED
```
with
```python
    COL0, COL1 = MASTHEAD_LEFT_WIDTH.twips, MASTHEAD_RIGHT_WIDTH.twips
```
and import `from tme_template.layout import MASTHEAD_LEFT_WIDTH, MASTHEAD_RIGHT_WIDTH` at the top; import `find_body_start_index` is already there.

- [ ] **Step 5: Run the suite**

Run: `cd tme_editor_app && python3 -m pytest tests -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add tme_editor_app/src/apply_styles.py tme_editor_app/src/fixup.py tme_editor_app/src/article_starter.py tme_editor_app/tests/test_structure_detection.py
git commit -m "find body start and cover tables by starter structure; derive masthead grid from layout"
```

---

### Task 4: Classification plumbing — duplicate cleaner, deterministic headings, reported Gemini output

**Files:**
- Modify: `tme_editor_app/src/apply_styles.py`
- Modify: `tme_editor_app/src/classifier.py`
- Test: `tme_editor_app/tests/test_cover_duplicates.py` (new)
- Test: `tme_editor_app/tests/test_classifier_parsing.py` (new)

**Interfaces:**
- Produces: `classifier.parse_classifications(raw_json: str, n: int) -> tuple[list[str], dict]` with report keys `missing` (int), `invalid` (int), `duplicates` (int).
- Produces: `classifier.classify_paragraphs_with_report(texts, *, title="", abstract="", api_key=None, model="gemini-2.5-flash") -> tuple[list[str], dict]`; `classify_paragraphs` stays as a wrapper returning labels only.
- `apply_styles` stats gain `"classifier_report"` (the dict above, or `{}`) and `"deleted_preamble_previews"` (list of up to 80-char strings).

- [ ] **Step 1: Write the failing tests**

`tests/test_cover_duplicates.py`:

```python
"""The top-of-body cleaner removes pasted cover duplicates and nothing else."""
import apply_styles
from extractor import ArticleMeta, AuthorMeta

META = ArticleMeta(
    title="Integration by Substitution: An Emergent Quantitative Reasoning Approach to U-Substitution",
    authors=[AuthorMeta(name="Kevin C. Moore")],
    affiliations=["Department of Mathematics and Science Education, University of Georgia"],
    abstract="We present a conceptual analysis of integration by substitution grounded in quantitative reasoning.",
)


def _dup(text):
    return apply_styles._looks_like_cover_duplicate(text, META)


def test_real_body_openers_survive():
    assert not _dup("Quantitative Reasoning")                                   # heading inside the title
    assert not _dup("Published research on u-substitution has largely focused on procedures.")
    assert not _dup("Department of Mathematics faculty participated in the study.")
    assert not _dup("Accepted practice in calculus instruction emphasizes procedures.")


def test_genuine_cover_duplicates_are_caught():
    assert _dup(META.title)
    assert _dup(META.title + "1")                                              # with affiliation mark
    assert _dup("Abstract")
    assert _dup("Keywords: calculus, quantitative reasoning")
    assert _dup("Received: March 3, 2026")
    assert _dup("Accepted 12 May 2026")
    assert _dup(META.abstract)
    assert _dup("Kevin C. Moore")
    assert _dup(META.affiliations[0])
    assert _dup("† Corresponding author: kvcmoore@uga.edu")
```

`tests/test_classifier_parsing.py`:

```python
"""Gemini output parsing is strict about shape and honest about gaps."""
import json

from classifier import parse_classifications


def _raw(items):
    return json.dumps({"classifications": items})


def test_complete_valid_reply():
    labels, report = parse_classifications(_raw([{"i": 1, "label": "heading_1"}, {"i": 2, "label": "body"}]), 2)
    assert labels == ["heading_1", "body"]
    assert report == {"missing": 0, "invalid": 0, "duplicates": 0}


def test_missing_and_invalid_are_counted_not_hidden():
    labels, report = parse_classifications(_raw([{"i": 1, "label": "nonsense"}]), 3)
    assert labels == ["body", "body", "body"]
    assert report == {"missing": 2, "invalid": 1, "duplicates": 0}


def test_duplicate_indices_count_once_and_last_wins():
    labels, report = parse_classifications(_raw([{"i": 1, "label": "body"}, {"i": 1, "label": "heading_2"}]), 1)
    assert labels == ["heading_2"]
    assert report["duplicates"] == 1 and report["missing"] == 0


def test_garbage_items_are_invalid_not_fatal():
    labels, report = parse_classifications(_raw([{"i": "x", "label": "body"}, "junk"]), 1)
    assert labels == ["body"] and report["invalid"] == 2 and report["missing"] == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tme_editor_app && python3 -m pytest tests/test_cover_duplicates.py tests/test_classifier_parsing.py -q`
Expected: duplicates test fails on the three false positives; parsing tests fail with ImportError.

- [ ] **Step 3: classifier.py**

Replace everything from `client = genai.Client(api_key=key)` to the end with:

```python
    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": _ClassificationResponse,
            "temperature": 0,
            # Disable "thinking" — classification is a pattern-match task,
            # not a reasoning task. Cuts latency by ~3-5×.
            "thinking_config": {"thinking_budget": 0},
        },
    )
    return parse_classifications(resp.text, len(paragraph_texts))


def classify_paragraphs(paragraph_texts, **kwargs) -> List[str]:
    """Labels only; see classify_paragraphs_with_report for the gap report."""
    return classify_paragraphs_with_report(paragraph_texts, **kwargs)[0]


def parse_classifications(raw_json: str, n: int) -> tuple[List[str], dict]:
    """Turn the model's JSON into one label per paragraph plus a report of
    what had to be patched: `missing` indices default to body, `invalid`
    items (bad index or unknown label) default to body, `duplicates` are
    counted and the last one wins."""
    data = json.loads(raw_json)
    items = data.get("classifications", []) if isinstance(data, dict) else []
    by_idx: dict[int, str] = {}
    invalid = duplicates = 0
    for item in items:
        try:
            i = int(item["i"])
            label = str(item.get("label", ""))
        except (TypeError, ValueError, KeyError):
            invalid += 1
            continue
        if label not in VALID_LABELS:
            invalid += 1
            label = "body"
        if i in by_idx:
            duplicates += 1
        by_idx[i] = label
    labels = [by_idx.get(i, "body") for i in range(1, n + 1)]
    missing = sum(1 for i in range(1, n + 1) if i not in by_idx)
    return labels, {"missing": missing, "invalid": invalid, "duplicates": duplicates}
```

Rename the existing function header `def classify_paragraphs(` to `def classify_paragraphs_with_report(` and change its return annotation to `-> tuple[List[str], dict]`. Add near the top (after `VALID_LABELS`):

```python
from pydantic import BaseModel


class _ClassificationItem(BaseModel):
    i: int
    label: str


class _ClassificationResponse(BaseModel):
    """Shape enforced by the SDK via response_schema."""
    classifications: list[_ClassificationItem]
```

Note the `"junk"` item: `"junk"["i"]` raises `TypeError`, which the except clause catches as invalid.

- [ ] **Step 4: apply_styles.py**

Replace `_looks_like_cover_duplicate` with:

```python
from difflib import SequenceMatcher

# "Received: March 3, 2026", "Accepted 12 May 2026", "Published online June 2026"
_DATE_LINE = re.compile(
    r"^(received|revised|accepted|published)\b[^\d]{0,20}\d", re.I)


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _looks_like_cover_duplicate(text: str, meta) -> bool:
    """True if a paragraph at the top of the pasted body duplicates cover
    content the starter already renders. Matches are near-equalities or
    whole-string containment, never prefixes: a heading that happens to be a
    phrase of the title, or a sentence that opens with 'Published', is body."""
    t = text.strip()
    if not t:
        return False
    tl = t.lower()
    title = (meta.title or "").strip()
    if title and (_similar(t, title) >= 0.85 or (title.lower() in tl and len(t) <= len(title) + 40)):
        return True
    abstract = (meta.abstract or "").strip()
    if abstract and len(t) >= 40 and _similar(t[:160], abstract[:160]) >= 0.85:
        return True
    if tl in {"abstract", "abstract:", "keywords", "keywords:"} or tl.startswith(("keywords:", "keywords ")):
        return True
    for a in meta.authors or []:
        if a.name and a.name.strip().lower() in tl and len(t) < 200:
            return True
    if _DATE_LINE.match(t):
        return True
    for aff in meta.affiliations or []:
        if aff and aff.strip().lower() in tl and len(t) < 200:
            return True
    if "corresponding author" in tl and len(t) < 200:
        return True
    return False
```

In the preamble loop, record what is removed:

```python
    deleted_preamble = 0
    deleted_previews = []
    ...
        if not t or is_placeholder or _looks_like_cover_duplicate(t, meta):
            if t and not is_placeholder:
                deleted_previews.append(t[:80])
            p._element.getparent().remove(p._element)
```
and add `"deleted_preamble_previews": deleted_previews,` plus `"classifier_report": {},` to the stats dict.

Deterministic source styles in the first pass, before the `Caption` check:

```python
        if src_style in ("Heading 1", "heading 1"):
            _assign(p, doc, "TME H1", stats); continue
        if src_style in ("Heading 2", "heading 2"):
            _assign(p, doc, "TME H2", stats); continue
        if src_style in ("Heading 3", "heading 3"):
            _assign(p, doc, "TME H3", stats); continue
        if src_style.startswith("TME ") and src_style != "TME Body":
            # The editor set this in Word (or a previous Finalize did); final.
            stats["applied"][src_style] = stats["applied"].get(src_style, 0) + 1
            continue
```
(`TME Body` paragraphs still go to the classifier: a re-finalized proof's body may contain headings the first pass missed.)

Use the report version of the classifier:

```python
            from classifier import classify_paragraphs_with_report
            labels, report = classify_paragraphs_with_report(
                pending_texts, title=meta.title or "", abstract=meta.abstract or "")
            stats["classifier"] = "gemini"
            stats["classifier_report"] = report
```

- [ ] **Step 5: Run the suite**

Run: `cd tme_editor_app && python3 -m pytest tests -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add tme_editor_app/src/apply_styles.py tme_editor_app/src/classifier.py tme_editor_app/tests/test_cover_duplicates.py tme_editor_app/tests/test_classifier_parsing.py
git commit -m "classification: typed Gemini schema with gap report, safer cover-duplicate cleaner, deterministic headings"
```

---

### Task 5: Fixup heuristics — block quotes, caption swap, header rows

**Files:**
- Modify: `tme_editor_app/src/fixup.py` (`remap_block_quotes`, `swap_captions_above`, `fix_content_tables`)
- Modify: `tme_editor_app/app.py:251-258` (pass the fresh report in the new order — see Step 3)
- Test: `tme_editor_app/tests/test_fixup_heuristics.py` (new)

**Interfaces:**
- `remap_block_quotes(doc)`: a TME Body paragraph becomes a block quote only with left indent > 20pt AND at least 40 words (APA's block-quote threshold).
- `swap_captions_above(doc, report)`: resolves each entry by its `index` against the current document, processing entries from the highest index down so earlier indices stay valid; for figures the preceding element must be an image paragraph.
- `fix_content_tables`: `tblHeader` only when the table has 2+ rows and every cell of row one has text.

- [ ] **Step 1: Write the failing tests**

```python
"""Fixup heuristics: block quotes need length, caption swap is index-exact,
header rows are only marked when they look like headers."""
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

import fixup
from tme_template.styles import (
    register_body_style, register_title_style,
    register_heading_styles, register_remaining_styles,
)


def _doc():
    doc = Document()
    for f in (register_body_style, register_title_style, register_heading_styles, register_remaining_styles):
        f(doc)
    return doc


def _image_paragraph(doc):
    p = doc.add_paragraph("", style="TME Body")
    d = OxmlElement("w:drawing")
    d.append(OxmlElement("wp:inline"))
    p.add_run()._r.append(d)
    return p


def test_short_indented_task_part_is_not_a_block_quote():
    doc = _doc()
    p = doc.add_paragraph("(a) Sketch the graph of f on [0, 4].", style="TME Body")
    p.paragraph_format.left_indent = Pt(36)
    assert fixup.remap_block_quotes(doc) == 0
    assert p.style.name == "TME Body"


def test_long_indented_quotation_is_a_block_quote():
    doc = _doc()
    p = doc.add_paragraph(" ".join(["word"] * 45), style="TME Body")
    p.paragraph_format.left_indent = Pt(36)
    assert fixup.remap_block_quotes(doc) == 1
    assert p.style.name == "TME Block Quote"


def test_swap_moves_two_identically_prefixed_captions_correctly():
    doc = _doc()
    for n in (1, 2):
        _image_paragraph(doc)
        doc.add_paragraph(f"Figure {n}. Same prefix caption", style="TME Figure Caption")
    report = fixup.report_below_element_captions(doc)
    assert [r["index"] for r in report] == [1, 3]

    moved = fixup.swap_captions_above(doc, report)

    assert moved == 2
    texts = [p.text for p in doc.paragraphs]
    assert texts == ["Figure 1. Same prefix caption", "", "Figure 2. Same prefix caption", ""]


def test_swap_ignores_a_figure_entry_whose_predecessor_is_text():
    doc = _doc()
    doc.add_paragraph("Just text.", style="TME Body")
    doc.add_paragraph("Figure 1. Not below an image", style="TME Figure Caption")
    fake = [{"index": 1, "kind": "figure", "preview": "Figure 1."}]
    assert fixup.swap_captions_above(doc, fake) == 0


def test_header_row_only_when_it_looks_like_one():
    doc = _doc()
    one_row = doc.add_table(rows=1, cols=2)
    one_row.cell(0, 0).text = "a"
    layout = doc.add_table(rows=2, cols=2)          # first row has an empty cell
    layout.cell(0, 0).text = "img"
    data = doc.add_table(rows=2, cols=2)
    for c in data.rows[0].cells:
        c.text = "head"

    fixup.fix_content_tables(doc, skip_indices=())

    def has_header(t):
        return t._tbl.findall(qn("w:tr"))[0].find(qn("w:trPr") + "/" + qn("w:tblHeader")) is not None
    assert not has_header(one_row) and not has_header(layout) and has_header(data)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tme_editor_app && python3 -m pytest tests/test_fixup_heuristics.py -q`
Expected: FAIL on the task-part test, the swap tests, and the header-row test.

- [ ] **Step 3: Implement**

`remap_block_quotes`: replace `if li.pt > 20:` with

```python
        # APA defines a block quote as 40+ words; indented short lines are
        # task parts, list continuations or equations.
        if li.pt > 20 and len(p.text.split()) >= 40:
```

`swap_captions_above`: replace the target-resolution block (from `for entry in report:` through `if target_p is None: continue`) with

```python
    paras = list(doc.paragraphs)
    for entry in sorted(report, key=lambda e: e["index"], reverse=True):
        kind = entry["kind"]
        idx = entry["index"]
        if idx >= len(paras):
            continue
        target_p = paras[idx]
        sn = target_p.style.name if target_p.style is not None else ""
        if (kind == "figure" and sn != "TME Figure Caption") or (kind == "table" and sn != "TME Table Caption"):
            continue
```
and replace the predecessor checks

```python
        if kind == "figure" and prev.tag != tag_p:
            continue
```
with
```python
        if kind == "figure" and (prev.tag != tag_p or not _has_image(prev)):
            continue
```
Update the docstring: entries are resolved by `index` against the document as it was when the report was generated; processing from the highest index down keeps the lower indices valid because a move only reorders elements between the caption and its figure. Remove the `preview`-matching sentences.

`fix_content_tables`: replace

```python
        if rows:
            _set_trPr_flag(rows[0], "tblHeader")
```
with
```python
        # Repeat the first row on page breaks only when it reads as a header:
        # two or more rows and text in every first-row cell. Layout tables
        # (images in cells) and one-row tables are left alone.
        first_cells = rows[0].findall(qn("w:tc")) if rows else []
        if len(rows) >= 2 and first_cells and all(
                "".join(t.text or "" for t in tc.iter(qn("w:t"))).strip() for tc in first_cells):
            _set_trPr_flag(rows[0], "tblHeader")
```

`app.py:251-258` already generates the report inside `run_fixup` and passes it straight to `swap_captions_above`; no change needed beyond confirming the `below` list still carries `index` entries (it does: `report_below_element_captions` sets `"index"`).

- [ ] **Step 4: Run the suite**

Run: `cd tme_editor_app && python3 -m pytest tests -q`
Expected: all pass (the earlier `test_fixup_captions.py` swap test still passes because it generates a fresh report).

- [ ] **Step 5: Commit**

```bash
git add tme_editor_app/src/fixup.py tme_editor_app/tests/test_fixup_heuristics.py
git commit -m "fixup: 40-word block quotes, index-exact caption swap, header rows only when they look like one"
```

---

### Task 6: Session resilience and UI reporting

**Files:**
- Create: `tme_editor_app/src/session_meta.py`
- Modify: `tme_editor_app/src/pipeline.py` (embed meta; return `PipelineResult`; no double JPEG)
- Modify: `tme_editor_app/app.py` (whole file)
- Test: `tme_editor_app/tests/test_session_meta.py` (new)
- Test: `tme_editor_app/tests/test_app_smoke.py` (new)

**Interfaces:**
- Produces: `session_meta.meta_to_json(meta) -> str`, `meta_from_json(s) -> ArticleMeta` (unknown keys ignored), `embed_meta(docx_path, meta) -> None` (writes `core_properties.comments`), `read_meta(docx_path) -> ArticleMeta | None`.
- Produces: `pipeline.PipelineResult(starter_path: Path, no_face_authors: list[str])`; `run_pipeline(...) -> PipelineResult`.
- Consumes: `author_cite_text` (Task 3), `classifier_report` and `deleted_preamble_previews` stats (Task 4), `frame_headshot_square -> bool` (template plan Task 1; if that plan has not landed, `bool(None)` is False and the warning simply lists every author — acceptable until both plans merge).

- [ ] **Step 1: Write the failing tests**

`tests/test_session_meta.py`:

```python
"""ArticleMeta rides inside the starter so Phase 2 can recover it."""
from docx import Document

from extractor import ArticleMeta, AuthorMeta
from session_meta import embed_meta, meta_from_json, meta_to_json, read_meta


def _meta():
    return ArticleMeta(title="T", authors=[AuthorMeta(name="Ada Lovelace", corresponding=True)],
                       affiliations=["UGA"], abstract="a", keywords=["k"], volume=34, number=2)


def test_round_trip_through_json():
    m = meta_from_json(meta_to_json(_meta()))
    assert m == _meta()


def test_unknown_keys_from_a_newer_starter_are_ignored():
    s = meta_to_json(_meta()).replace('"title": "T"', '"title": "T", "future_field": 1')
    assert meta_from_json(s).title == "T"


def test_embed_and_read_back(tmp_path):
    path = tmp_path / "s.docx"
    Document().save(path)
    embed_meta(path, _meta())
    assert read_meta(path) == _meta()


def test_document_without_meta_reads_none(tmp_path):
    path = tmp_path / "plain.docx"
    Document().save(path)
    assert read_meta(path) is None
```

`tests/test_app_smoke.py`:

```python
"""The Streamlit page renders without raising (no Gemini call involved)."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_app_renders_without_exception():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
    headers = " ".join(h.value for h in at.header)
    assert "Phase 1" in headers and "Phase 2" in headers
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tme_editor_app && python3 -m pytest tests/test_session_meta.py tests/test_app_smoke.py -q`
Expected: session tests fail with ImportError; the smoke test fails because "Phase 2" is only rendered after a build today.

- [ ] **Step 3: session_meta.py**

```python
"""Carry ArticleMeta inside the starter .docx so Phase 2 can recover it after
the editor's browser session has expired (they leave for Word for hours).

The JSON lives in the core-properties Comments field (dc:description), which
Word preserves on save and which needs no custom XML part."""
import json
from dataclasses import asdict, fields

from docx import Document

from extractor import ArticleMeta, AuthorMeta

MARKER = "TME-META-JSON:"


def meta_to_json(meta: ArticleMeta) -> str:
    return json.dumps(asdict(meta), ensure_ascii=False)


def _only_known(cls, d: dict) -> dict:
    names = {f.name for f in fields(cls)}
    return {k: v for k, v in d.items() if k in names}


def meta_from_json(s: str) -> ArticleMeta:
    d = _only_known(ArticleMeta, json.loads(s))
    d["authors"] = [AuthorMeta(**_only_known(AuthorMeta, a)) for a in d.get("authors", [])]
    return ArticleMeta(**d)


def embed_meta(docx_path, meta: ArticleMeta) -> None:
    doc = Document(str(docx_path))
    doc.core_properties.comments = MARKER + meta_to_json(meta)
    doc.save(str(docx_path))


def read_meta(docx_path):
    comments = Document(str(docx_path)).core_properties.comments or ""
    if not comments.startswith(MARKER):
        return None
    return meta_from_json(comments[len(MARKER):])
```

- [ ] **Step 4: pipeline.py**

```python
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
    """Run the full pipeline. The starter carries `meta` in its document
    properties so Phase 2 can recover it without the browser session."""
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
```

- [ ] **Step 5: app.py**

Replace the whole file with:

```python
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
from session_meta import read_meta

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
    "manuscript_sig": None,     # (name, size) of the upload we saved
    "starter_bytes": None,
    "proof_bytes": None,
    "proof_filename": None,
}
for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default
if "work_dir" not in st.session_state:
    st.session_state.work_dir = Path(tempfile.mkdtemp(prefix="tme_editor_"))


def _reset_session():
    shutil.rmtree(st.session_state.work_dir, ignore_errors=True)
    for key in list(st.session_state.keys()):
        del st.session_state[key]
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
ms = st.file_uploader("Submitted manuscript (.docx)", type=['docx'], key='ms_upload')
if ms is not None:
    sig = (ms.name, ms.size)
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
        "Headshot image files", type=HEADSHOT_TYPES, accept_multiple_files=True, key='headshots',
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
    "Upload your populated starter (after pasting body in Word)", type=['docx'], key='populated_upload',
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
                meta2 = st.session_state.meta or read_meta(proof_path)
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
```

- [ ] **Step 6: Run the suite**

Run: `cd tme_editor_app && python3 -m pytest tests -q`
Expected: all pass. The smoke test exercises the real script; if it reports an exception, read `at.exception[0].value` and fix the script.

- [ ] **Step 7: Commit**

```bash
git add tme_editor_app/src/session_meta.py tme_editor_app/src/pipeline.py tme_editor_app/app.py tme_editor_app/tests/test_session_meta.py tme_editor_app/tests/test_app_smoke.py
git commit -m "app: metadata rides in the starter, reset and re-upload, stable headshot keys, honest warnings"
```

---

### Task 7: Extractor — typed schema, whole manuscript, validation, current-year default

**Files:**
- Modify: `tme_editor_app/src/extractor.py`
- Test: `tme_editor_app/tests/test_extractor.py` (new)

**Interfaces:**
- Produces: `extractor.to_article_meta(data: dict) -> ArticleMeta` (lenient: None → default, affiliation_num clamped to `1..max(1, len(affiliations))`, non-dict authors dropped).
- `extract_manuscript_text(docx_path, max_chars=None)`: whole text by default.
- `ArticleMeta.year` defaults to the current year.

- [ ] **Step 1: Write the failing tests**

```python
"""Metadata parsing is lenient about nulls and the whole manuscript is read."""
from datetime import date

from docx import Document

import extractor
from extractor import ArticleMeta, extract_manuscript_text, to_article_meta


def test_nulls_and_bad_indices_become_safe_defaults():
    meta = to_article_meta({
        "title": None,
        "authors": [{"name": None, "affiliation_num": 7, "bio": None, "email": None, "corresponding": None},
                    "not a dict"],
        "affiliations": ["X"],
        "abstract": None, "keywords": None,
        "received": None, "revised": None, "accepted": None, "published": None, "doi": None,
    })
    assert meta.title == "" and meta.abstract == "" and meta.keywords == []
    assert len(meta.authors) == 1
    assert meta.authors[0].name == "" and meta.authors[0].affiliation_num == 1
    assert meta.authors[0].corresponding is False


def test_year_defaults_to_this_year():
    assert ArticleMeta().year == date.today().year


def test_whole_manuscript_is_read(tmp_path):
    path = tmp_path / "long.docx"
    doc = Document()
    for i in range(400):
        doc.add_paragraph("x" * 100 + f" {i}")
    doc.add_paragraph("AUTHOR BIO AT THE END")
    doc.save(path)
    assert extract_manuscript_text(str(path)).endswith("AUTHOR BIO AT THE END")


def test_response_schema_is_passed_to_gemini(monkeypatch):
    captured = {}

    class _Resp:
        text = '{"title": "T", "authors": [], "affiliations": [], "abstract": "", "keywords": [], "received": "", "revised": "", "accepted": "", "published": "", "doi": ""}'

    class _Models:
        def generate_content(self, **kw):
            captured.update(kw)
            return _Resp()

    class _Client:
        def __init__(self, api_key):
            self.models = _Models()

    monkeypatch.setattr(extractor.genai, "Client", _Client)
    meta = extractor.extract_metadata("text", api_key="k")
    assert meta.title == "T"
    assert captured["config"]["response_schema"] is extractor.MetadataSchema
```

- [ ] **Step 2: Run to verify failure**

Run: `cd tme_editor_app && python3 -m pytest tests/test_extractor.py -q`
Expected: FAIL (ImportError on `to_article_meta`; year 2026 hard-coded; text truncated).

- [ ] **Step 3: Rewrite the relevant parts of extractor.py**

Imports: add `from datetime import date` and `from pydantic import BaseModel`; keep `import google.genai as genai`.

`ArticleMeta.year`: `year: int = field(default_factory=lambda: date.today().year)`.

`extract_manuscript_text`:

```python
def extract_manuscript_text(docx_path: str, max_chars: int | None = None) -> str:
    """Plain text of a .docx, preserving paragraph breaks. The whole document
    by default: author bios and dates often sit after the references, and
    Gemini 2.5 Flash's context holds any manuscript comfortably."""
    ...
        paragraphs.append(line)
        total += len(line) + 1
        if max_chars is not None and total >= max_chars:
            break
    return '\n'.join(paragraphs)
```

Schema and lenient conversion:

```python
class AuthorSchema(BaseModel):
    name: str
    affiliation_num: int
    bio: str
    email: str
    corresponding: bool


class MetadataSchema(BaseModel):
    """Shape the SDK enforces on Gemini's reply (response_schema)."""
    title: str
    authors: list[AuthorSchema]
    affiliations: list[str]
    abstract: str
    keywords: list[str]
    received: str
    revised: str
    accepted: str
    published: str
    doi: str


def _s(v) -> str:
    return v if isinstance(v, str) else ""


def _list_of_str(v) -> list:
    return [x for x in v if isinstance(x, str)] if isinstance(v, list) else []


def to_article_meta(data: dict) -> ArticleMeta:
    """Lenient conversion: the schema asks for strings and ints, but a model
    reply can still carry nulls or odd values, and an explicit null bypasses
    dict.get defaults. Nothing here raises on bad shape."""
    affiliations = _list_of_str(data.get("affiliations"))
    max_aff = max(1, len(affiliations))
    authors = []
    for a in data.get("authors") or []:
        if not isinstance(a, dict):
            continue
        try:
            aff = int(a.get("affiliation_num") or 1)
        except (TypeError, ValueError):
            aff = 1
        authors.append(AuthorMeta(
            name=_s(a.get("name")).strip(),
            affiliation_num=min(max(aff, 1), max_aff),
            bio=_s(a.get("bio")),
            email=_s(a.get("email")).strip() or None,
            corresponding=bool(a.get("corresponding")),
        ))
    return ArticleMeta(
        title=_s(data.get("title")).strip(),
        authors=authors,
        affiliations=affiliations,
        abstract=_s(data.get("abstract")),
        keywords=_list_of_str(data.get("keywords")),
        received=_s(data.get("received")),
        revised=_s(data.get("revised")),
        accepted=_s(data.get("accepted")),
        published=_s(data.get("published")),
        doi=_s(data.get("doi")),
    )


def extract_metadata(manuscript_text: str, api_key: Optional[str] = None) -> ArticleMeta:
    """Call Gemini Flash to extract structured metadata. Raises on API / JSON
    errors (caller surfaces them)."""
    key = api_key or os.environ.get('GEMINI_API_KEY')
    if not key:
        raise RuntimeError('GEMINI_API_KEY not set')
    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=EXTRACTION_PROMPT + manuscript_text,
        config={'response_mime_type': 'application/json', 'response_schema': MetadataSchema},
    )
    return to_article_meta(json.loads(resp.text))
```

In `EXTRACTION_PROMPT`, change `"email": "email if given, else null"` to `"email": "email if given, else empty string"` so the prompt agrees with the schema.

- [ ] **Step 4: Run the suite**

Run: `cd tme_editor_app && python3 -m pytest tests -q`
Expected: all pass (the citation tests pass `year=2026` explicitly, so the new default does not affect them).

- [ ] **Step 5: Commit**

```bash
git add tme_editor_app/src/extractor.py tme_editor_app/tests/test_extractor.py
git commit -m "extractor: typed Gemini schema, lenient parsing, whole manuscript, current-year default"
```

---

### Task 8: Golden end-to-end test

**Files:**
- Test: `tme_editor_app/tests/test_golden_pipeline.py` (new)

**Interfaces:**
- Consumes everything above: `build_article_starter`, `apply_styles`, `run_fixup`, `classify_paragraphs_with_report` (monkeypatched).

- [ ] **Step 1: Write the test**

```python
"""Build a starter, paste a synthetic body, run both phases with a fixed
classifier, and check every paragraph's style and the untouched cover."""
from pathlib import Path

import pytest
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

import classifier
from apply_styles import apply_styles
from article_starter import build_article_starter
from extractor import ArticleMeta, AuthorMeta
from fixup import run_fixup

HYPERLINK_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"

META = ArticleMeta(
    title="Expanding the Scope of Unit Transformation Graphs",
    authors=[AuthorMeta(name="Joseph Antonides", bio="bio"), AuthorMeta(name="Anderson Norton", bio="bio")],
    affiliations=["Virginia Tech"], abstract="We extend UTGs.", keywords=["UTG"], year=2026,
)

LABELS = {
    "Introduction": "heading_1",
    "Figure 1 depicts a UTG of a hypothetical solution to the Cake Task.": "body",
    "Table 2 presents the coding scheme used in this study.": "body",
    "Figure 1": "skip",
    "UTG for the Cake Task": "caption_figure",
    "Students' Mathematics": "heading_2",
    "Antonides, J., & Norton, A. (2023). Units. Journal, 1(1), 1–2. ": "reference",
    "(a) Sketch the graph.": "body",
}


def _fake_classifier(texts, **kwargs):
    return [LABELS.get(t.strip(), "body") for t in texts], {"missing": 0, "invalid": 0, "duplicates": 0}


def _hyperlink(p, text):
    r_id = p.part.relate_to("https://doi.org/10.1/x", HYPERLINK_REL, is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), r_id)
    r = OxmlElement("w:r"); rPr = OxmlElement("w:rPr"); f = OxmlElement("w:rFonts")
    f.set(qn("w:ascii"), "Times New Roman"); rPr.append(f); r.append(rPr)
    t = OxmlElement("w:t"); t.text = text; r.append(t); h.append(r); p._p.append(h)
    return r


def _paste_body(path):
    doc = Document(path)
    doc.add_paragraph("Expanding the Scope of Unit Transformation Graphs")      # pasted title (duplicate)
    doc.add_paragraph("Introduction")
    doc.add_paragraph("Figure 1 depicts a UTG of a hypothetical solution to the Cake Task.")
    doc.add_paragraph("Table 2 presents the coding scheme used in this study.")
    doc.add_paragraph("Figure 1")
    doc.add_paragraph("UTG for the Cake Task")
    img = doc.add_paragraph()
    d = OxmlElement("w:drawing"); d.append(OxmlElement("wp:inline")); img.add_run()._r.append(d)
    doc.add_paragraph("Students' Mathematics")
    ref = doc.add_paragraph("Antonides, J., & Norton, A. (2023). Units. Journal, 1(1), 1–2. ")
    ref.paragraph_format.first_line_indent = Pt(-18); ref.paragraph_format.left_indent = Pt(18)
    _hyperlink(ref, "https://doi.org/10.1/x")
    task = doc.add_paragraph("(a) Sketch the graph.")
    task.paragraph_format.left_indent = Pt(36)
    t = doc.add_table(rows=2, cols=2)
    for c in t.rows[0].cells: c.text = "Head"
    t.cell(1, 0).text = "v"
    doc.save(path)


def test_golden_pipeline(tmp_path, monkeypatch):
    monkeypatch.setattr(classifier, "classify_paragraphs_with_report", _fake_classifier)
    path = tmp_path / "proof.docx"
    build_article_starter(meta=META, headshots={}, out_path=path)
    card_xml_before = Document(path).tables[2]._tbl.xml
    _paste_body(path)

    style_stats = apply_styles(str(path), META)
    fixup_stats = run_fixup(str(path))

    doc = Document(path)
    body = {p.text: p for p in doc.paragraphs}
    assert style_stats["classifier"] == "gemini"
    assert style_stats["deleted_preamble_previews"] == ["Expanding the Scope of Unit Transformation Graphs"]
    assert body["Introduction"].style.name == "TME H1"
    assert body["Students' Mathematics"].style.name == "TME H2"
    assert body["Figure 1 depicts a UTG of a hypothetical solution to the Cake Task."].style.name == "TME Body"
    assert body["Table 2 presents the coding scheme used in this study."].style.name == "TME Body"
    assert body["Figure 1. UTG for the Cake Task"].style.name == "TME Figure Caption"
    assert body["(a) Sketch the graph."].style.name == "TME Body"
    img_para = [p for p in doc.paragraphs if p._p.find(".//" + qn("w:drawing")) is not None][-1]
    assert img_para.alignment == WD_ALIGN_PARAGRAPH.CENTER
    ref_para = next(p for p in doc.paragraphs if p.text.startswith("Antonides, J."))
    assert ref_para.style.name == "TME Reference"
    link_runs = ref_para._p.findall(".//" + qn("w:hyperlink") + "/" + qn("w:r"))
    assert link_runs and all(r.find(qn("w:rPr") + "/" + qn("w:rFonts")) is None for r in link_runs)
    assert doc.tables[2]._tbl.xml == card_xml_before            # author card untouched
    content = doc.tables[3]
    assert all(p.style.name == "TME Table Text" for row in content.rows for c in row.cells for p in c.paragraphs)
    assert content._tbl.findall(qn("w:tr"))[0].find(qn("w:trPr") + "/" + qn("w:tblHeader")) is not None
    assert fixup_stats["split_captions"] == {"labels_restyled": 1, "titles_merged": 1}
```

- [ ] **Step 2: Run it**

Run: `cd tme_editor_app && python3 -m pytest tests/test_golden_pipeline.py -q`
Expected: PASS. If a single assertion fails, that is a real defect in an earlier task: fix the module, not the test, unless the test's expectation is wrong against the spec.

- [ ] **Step 3: Run everything and commit**

Run: `cd tme_editor_app && python3 -m pytest tests -q`
Expected: all pass.

```bash
git add tme_editor_app/tests/test_golden_pipeline.py
git commit -m "golden end-to-end test: starter + pasted body through apply_styles and fixup"
```

---

## Self-review notes

- Spec coverage: A2 → Task 6; A3 → Tasks 4 and 6; A4 → Task 3; A5 → Task 4; A6 → Task 2; A7 → Task 2 (+ Task 3 for skip indices); A8 → Task 3; A9 → Task 2; A10 → Task 6 (pipeline) and `HEADSHOT_TYPES`; A11 → Task 6; A12, A13 → Task 7; A14, A15 → Tasks 5 and 4; nits (running header helper, duplicated filename helpers, widget keys, year default, footnote symbol fonts, swap identity, tblHeader, masthead twips, dead `_style()`) → Tasks 2, 3, 5, 6, 7; Dockerfile, README, dead smoke test, moore_build → Task 1; golden test → Task 8.
- Not done on purpose: `REF_PAT`/`_REF_OPENER` broadening (lowercase particles, corporate authors) — widening the reference matcher risks turning body sentences into references; left for a separate change with real reference lists to test against. The caption `keep_with_next` nit depends on caption position and is covered by the swap option.
- `_style()` in apply_styles.py is unused; delete it in Task 4 while editing the file.
