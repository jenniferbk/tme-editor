# Template Package Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix every template-package finding from the 7 Oct 2026 code review (T1–T13, template nits, template test gaps) without changing the cover's visible layout.

**Architecture:** `template_build/src/tme_template/` is a library of small builders over python-docx. Each task fixes one module group, adds tests that pin the behavior, and leaves the public builder signatures intact except where a parameter was dead. A schema-order checker in the tests catches out-of-order OOXML for good.

**Tech Stack:** Python 3.11+, python-docx 1.2.0 (installed), Pillow 12, opencv-python-headless 4.x (<5), pytest. Run tests with the Homebrew `python3` from `template_build/`.

**Spec:** `docs/code-review-2026-10-07.md` (findings prefixed T, the "Template package" nits, and the template paragraph under Tests).

## Global Constraints

- Edit only files under `template_build/`. Another plan edits `tme_editor_app/`, `requirements.txt`, `README.md` and the Dockerfile at the same time; do not touch them.
- `template_build/src/tme_template/layout.py` already exists and is the single source of page geometry: `PAGE_WIDTH_IN = 8.5`, `BLEED_IN = 0.063`, `MASTHEAD_LOGO_FRACTION = 0.38`, `MASTHEAD_LEFT_WIDTH`, `MASTHEAD_RIGHT_WIDTH`, `FULL_BLEED_WIDTH` (python-docx `Length`s). Import from it; never redefine those numbers.
- The zero-margin-section bleed design and the current effective page margins stay as they are (owner decision). Do not change `configure_zero_margins`, the bleed, or margin values.
- The TME H1 left indent is dropped (owner decision); no red rule is added.
- `opencv-python-headless` stays `<5` everywhere it is pinned.
- Never write `TME_Template_2026.docx` at the repo root from a test; build into `tmp_path`.
- Run the suite with `cd template_build && python3 -m pytest tests -q` after every task; it must stay green.
- Commit after each task. Subject line in the imperative, under 70 characters; end the message with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

## Review Focus

Inputs the spec implies but no finding spells out. Each has a test in the task named.

1. A grayscale (mode "L") JPEG headshot must come out as a normal RGB crop, not crash in OpenCV's RGB2GRAY. Test in Task 1.
2. A masthead with `doi=None` must not render a blank line in the red panel. Test in Task 4.
3. An author card with four authors must give each cell 7.5/4 inches and the widths must agree between grid and cells. Test in Task 4.
4. A paragraph that receives a bottom rule after its spacing and indent were set must still produce schema-ordered pPr. Test in Task 3.
5. The research-article masthead section in a built template must carry both a default and an even footer reference. Test in Task 7.

---

### Task 1: Headshot input handling

**Files:**
- Modify: `template_build/src/tme_template/headshot.py` (whole module)
- Test: `template_build/tests/test_headshot_inputs.py` (new)

**Interfaces:**
- Produces: `frame_headshot_square(src_path, out_path, size_px=300, circle=True, bg_rgb=(255,255,255)) -> bool` (True when a face was detected and used; False when the heuristic crop was used). Callers that ignore the return value keep working.
- Produces: `load_headshot(src_path, bg_rgb=(255,255,255)) -> PIL.Image.Image` and `circle_mask(size_px, supersample=4) -> PIL.Image.Image`.

- [ ] **Step 1: Write the failing tests**

```python
"""Headshot input handling: EXIF orientation, transparency, mask quality,
cascade load check, grayscale input, face-found return value."""
import cv2
import pytest
from PIL import Image

from tme_template import headshot
from tme_template.headshot import circle_mask, frame_headshot_square, load_headshot


def test_exif_orientation_is_applied_before_cropping(tmp_path):
    # Stored 200x100 landscape: left half red, right half blue, tagged
    # Orientation=6 (rotate 90° clockwise to display). Displayed correctly it
    # is a 100x200 portrait with red on top; the portrait heuristic crop keeps
    # the top, so pixel (90, 10) is red. Without the transpose the crop is the
    # middle of the landscape image and (90, 10) lands in the blue half.
    img = Image.new("RGB", (200, 100), "blue")
    img.paste("red", (0, 0, 100, 100))
    exif = img.getexif()
    exif[0x0112] = 6
    src = tmp_path / "phone.jpg"
    img.save(src, exif=exif)
    out = tmp_path / "out.jpg"

    frame_headshot_square(str(src), str(out), size_px=100, circle=False)

    r, g, b = Image.open(out).getpixel((90, 10))
    assert r > 200 and b < 80


def test_transparent_png_is_flattened_onto_background(tmp_path):
    src = tmp_path / "cutout.png"
    Image.new("RGBA", (120, 120), (0, 0, 0, 0)).save(src)
    out = tmp_path / "out.jpg"

    frame_headshot_square(str(src), str(out), size_px=60, circle=False, bg_rgb=(255, 255, 255))

    r, g, b = Image.open(out).getpixel((30, 30))
    assert min(r, g, b) > 245  # white within JPEG tolerance; used to be 0,0,0


def test_palette_png_with_transparency_is_flattened(tmp_path):
    src = tmp_path / "pal.png"
    Image.new("RGBA", (40, 40), (0, 0, 0, 0)).convert("P").save(src, transparency=0)
    assert load_headshot(src).getpixel((5, 5)) == (255, 255, 255)


def test_grayscale_jpeg_is_handled(tmp_path):
    src = tmp_path / "gray.jpg"
    Image.new("L", (100, 100), 128).save(src)
    out = tmp_path / "out.jpg"
    frame_headshot_square(str(src), str(out), size_px=50)
    assert Image.open(out).mode == "RGB"


def test_circle_mask_is_anti_aliased():
    values = set(circle_mask(64).getdata())
    assert values - {0, 255}, "edge should contain intermediate gray values"


def test_returns_whether_a_face_was_used(tmp_path):
    src = tmp_path / "flat.jpg"
    Image.new("RGB", (100, 140), "gray").save(src)
    assert frame_headshot_square(str(src), str(tmp_path / "o.jpg"), size_px=50) is False


def test_empty_cascade_raises_clearly(monkeypatch):
    class _Empty:
        def empty(self):
            return True

    monkeypatch.setattr(headshot, "_FACE_CASCADE", None)
    monkeypatch.setattr(cv2, "CascadeClassifier", lambda path: _Empty())
    with pytest.raises(RuntimeError, match="cascade"):
        headshot._get_face_cascade()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd template_build && python3 -m pytest tests/test_headshot_inputs.py -q`
Expected: ImportError on `circle_mask`/`load_headshot` (collection error) — that counts as failing.

- [ ] **Step 3: Rewrite headshot.py**

Replace the whole file with:

```python
"""Crop-and-resize author headshots to square, centered on the face when detectable."""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps


# Lazy-loaded cascade so import-time isn't penalized for callers that don't use detection
_FACE_CASCADE = None


def _get_face_cascade():
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        cascade = cv2.CascadeClassifier(str(cascade_path))
        if cascade.empty():
            raise RuntimeError(
                f"OpenCV face cascade failed to load from {cascade_path}; "
                "check the opencv-python-headless install (must be <5)."
            )
        _FACE_CASCADE = cascade
    return _FACE_CASCADE


def _detect_face_center(pil_img: Image.Image) -> tuple[int, int] | None:
    """Return (cx, cy) of the largest detected face, or None if no face found."""
    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
    # Scale the minimum face size with the image so small source photos can
    # still match; a fixed 60px floor never fires on a 200px thumbnail.
    min_side = max(24, min(pil_img.size) // 8)
    faces = _get_face_cascade().detectMultiScale(
        cv_img, scaleFactor=1.1, minNeighbors=5, minSize=(min_side, min_side))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return (x + w // 2, y + h // 2)


def _heuristic_crop(w: int, h: int) -> tuple[int, int, int]:
    """Fallback when no face is detected: top-bias for portraits, center for landscape."""
    side = min(w, h)
    left = (w - side) // 2
    if h > w:
        top = max(0, (h // 3) - (side // 2))
        top = min(top, h - side)
    else:
        top = (h - side) // 2
    return left, top, side


def _face_centered_crop(w: int, h: int, cx: int, cy: int) -> tuple[int, int, int]:
    """Square crop centered on (cx, cy), clamped to image bounds."""
    side = min(w, h)
    half = side // 2
    left = max(0, min(cx - half, w - side))
    top = max(0, min(cy - half, h - side))
    return left, top, side


def load_headshot(src_path, bg_rgb: tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    """Open an image the way a viewer shows it: EXIF orientation applied and
    any transparency flattened onto bg_rgb. Always returns an RGB image."""
    with Image.open(src_path) as raw:
        img = ImageOps.exif_transpose(raw)
        img.load()
    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
    if has_alpha:
        rgba = img.convert("RGBA")
        flat = Image.new("RGB", rgba.size, bg_rgb)
        flat.paste(rgba, mask=rgba.getchannel("A"))
        return flat
    return img.convert("RGB")


def circle_mask(size_px: int, supersample: int = 4) -> Image.Image:
    """Anti-aliased circular mask: drawn at supersample× and downsampled, so
    the circle edge is smooth instead of stepping from 255 to 0."""
    big = size_px * supersample
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, big - 1, big - 1), fill=255)
    return mask.resize((size_px, size_px), Image.Resampling.LANCZOS)


def frame_headshot_square(src_path: str, out_path: str, size_px: int = 300,
                          circle: bool = True,
                          bg_rgb: tuple[int, int, int] = (255, 255, 255)) -> bool:
    """Square-crop a headshot, centered on the face if detectable.

    When circle=True (default), paints everything outside an inscribed circle
    with bg_rgb — yielding a round-looking headshot on that background.
    Saved as JPEG (no alpha); bg_rgb should match the surrounding page color.

    Returns True when a face was detected and used for the crop, False when
    the top-biased heuristic crop was used, so callers can flag photos that
    deserve a manual look.
    """
    img = load_headshot(src_path, bg_rgb)
    w, h = img.size
    face = _detect_face_center(img)
    if face is not None:
        left, top, side = _face_centered_crop(w, h, *face)
    else:
        left, top, side = _heuristic_crop(w, h)
    cropped = img.crop((left, top, left + side, top + side))
    cropped = cropped.resize((size_px, size_px), Image.Resampling.LANCZOS)
    if circle:
        bg = Image.new("RGB", (size_px, size_px), bg_rgb)
        cropped = Image.composite(cropped, bg, circle_mask(size_px))
    cropped.save(out_path, "JPEG", quality=90)
    return face is not None
```

- [ ] **Step 4: Run the whole template suite**

Run: `cd template_build && python3 -m pytest tests -q`
Expected: all pass. If `tests/test_headshot.py` asserted the old `None` return, change that assertion to `is False` or `in (True, False)`.

- [ ] **Step 5: Commit**

```bash
git add template_build/src/tme_template/headshot.py template_build/tests/test_headshot_inputs.py template_build/tests/test_headshot.py
git commit -m "headshot: apply EXIF orientation, flatten alpha, smooth circle, report no-face"
```

---

### Task 2: Cover footer on even pages; explicit header/footer distance; native odd/even setting

**Files:**
- Modify: `template_build/src/tme_template/cover_footer.py`
- Modify: `template_build/src/tme_template/page_setup.py`
- Modify: `template_build/src/tme_template/oxml_helpers.py` (delete `set_different_odd_even_pages` and `set_different_first_page`)
- Test: `template_build/tests/test_page_setup_and_footer.py` (new)

**Interfaces:**
- `add_cover_footer(section, *, citation)` keeps its signature; it now fills `section.footer` and `section.even_page_footer`.
- `configure_page_setup(doc)` keeps its signature.

- [ ] **Step 1: Write the failing tests**

```python
"""Page setup and cover footer: odd/even on, distances explicit, footer on both parities."""
from docx import Document
from docx.shared import Inches

from tme_template.cover_footer import add_cover_footer
from tme_template.page_setup import configure_page_setup


def _footer_text(footer):
    return " ".join(p.text for t in footer.tables for c in t._cells for p in c.paragraphs)


def test_odd_even_setting_is_on_and_distances_are_explicit():
    doc = Document()
    configure_page_setup(doc)
    assert doc.settings.odd_and_even_pages_header_footer is True
    s = doc.sections[0]
    assert s.header_distance == Inches(0.5)
    assert s.footer_distance == Inches(0.5)


def test_cover_footer_is_defined_for_even_pages_too():
    doc = Document()
    configure_page_setup(doc)
    sec = doc.sections[0]

    add_cover_footer(sec, citation="Cite me.")

    assert "HOW TO CITE" in _footer_text(sec.footer)
    assert "HOW TO CITE" in _footer_text(sec.even_page_footer)
    assert sec.even_page_footer.is_linked_to_previous is False
    xml = sec._sectPr.xml
    assert 'w:type="default"' in xml and 'w:type="even"' in xml
```

- [ ] **Step 2: Run to verify failure**

Run: `cd template_build && python3 -m pytest tests/test_page_setup_and_footer.py -q`
Expected: both FAIL (`header_distance` is 457200 EMU = 0.5in already, but `even_page_footer` text is empty; the first test fails on `odd_and_even_pages_header_footer` only if the setting is read differently — if it passes, fine).

- [ ] **Step 3: page_setup.py**

Replace the file with:

```python
"""Configure page size, margins, and odd/even pages."""
from docx.shared import Inches

# Word keeps body text clear of header and footer content. With the header
# distance at 0.5" and a 0.3" top margin, the body actually starts about 0.7"
# down on pages that carry a running header. That is the layout the published
# proofs have shipped with, so the numbers are set explicitly here rather than
# inherited from python-docx's defaults. Tightening them is a design decision
# to make in Word, not a bug fix.
TOP_BOTTOM_MARGIN = Inches(0.3)
SIDE_MARGIN = Inches(0.5)
HEADER_FOOTER_DISTANCE = Inches(0.5)


def configure_page_setup(doc) -> None:
    """US Letter, 0.3" top/bottom and 0.5" side margins, odd/even pages distinct."""
    for section in doc.sections:
        section.page_width = Inches(8.5)
        section.page_height = Inches(11)
        section.top_margin = TOP_BOTTOM_MARGIN
        section.bottom_margin = TOP_BOTTOM_MARGIN
        section.left_margin = SIDE_MARGIN
        section.right_margin = SIDE_MARGIN
        section.header_distance = HEADER_FOOTER_DISTANCE
        section.footer_distance = HEADER_FOOTER_DISTANCE
    doc.settings.odd_and_even_pages_header_footer = True


def configure_zero_margins(section) -> None:
    """Set all four margins on a section to zero."""
    section.top_margin = Inches(0)
    section.bottom_margin = Inches(0)
    section.left_margin = Inches(0)
    section.right_margin = Inches(0)
```

- [ ] **Step 4: cover_footer.py — fill both footers**

Replace `add_cover_footer` and its body with:

```python
def add_cover_footer(section, *, citation: Citation) -> None:
    """Place the cover footer (HOW TO CITE + citation) in the given section's
    footer slots. Appears at the bottom of every page in this section. Since
    the cover section is exactly one page (continuous break above, next-page
    break after), it only appears on the cover page.

    Different odd/even pages is on document-wide (page_setup), and an
    assembled issue can put an article cover on an even page, so both the
    default (odd) and the even footer are filled.

    `citation` is either a plain string or a sequence of (text, italic)
    segments so the journal name and volume can be italicized per APA 7."""
    for footer in (section.footer, section.even_page_footer):
        footer.is_linked_to_previous = False
        _fill_cover_footer(footer, citation)


def _fill_cover_footer(footer, citation: Citation) -> None:
    for p in list(footer.paragraphs):
        p._p.getparent().remove(p._p)

    table = footer.add_table(rows=1, cols=1, width=Inches(7.5))
    table.autofit = False
    table.columns[0].width = Inches(7.5)
    table.cell(0, 0).width = Inches(7.5)
    force_table_full_width(table, total_width_inches=7.5, left_indent_inches=0.5)

    cell = table.cell(0, 0)
    remove_cell_borders(cell)
    set_cell_shading(cell, FOOTER_CREAM)
    set_cell_margins(cell, top=120, bottom=120, left=120, right=120)

    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.2
    r_label = p.add_run("HOW TO CITE  ")
    r_label.font.name = "Arial"
    r_label.font.size = Pt(8)
    r_label.font.bold = True
    r_label.font.color.rgb = RGBColor.from_string(UGA_RED)
    segments = [(citation, False)] if isinstance(citation, str) else citation
    for text, italic in segments:
        r_cite = p.add_run(text)
        r_cite.font.name = "Arial"
        r_cite.font.size = Pt(8)
        r_cite.font.color.rgb = RGBColor.from_string(TEXT_MUTED)
        if italic:
            r_cite.font.italic = True
```

- [ ] **Step 5: Delete the two dead helpers from oxml_helpers.py**

Remove `set_different_odd_even_pages` and `set_different_first_page` (lines 38–49). Run `grep -rn "set_different_odd_even_pages\|set_different_first_page" template_build tme_editor_app moore_build` and confirm the only hit left is none (page_setup.py no longer imports it).

- [ ] **Step 6: Run the suite**

Run: `cd template_build && python3 -m pytest tests -q`
Expected: all pass, including `test_cover_footer.py` from earlier.

- [ ] **Step 7: Commit**

```bash
git add template_build/src/tme_template/cover_footer.py template_build/src/tme_template/page_setup.py template_build/src/tme_template/oxml_helpers.py template_build/tests/test_page_setup_and_footer.py
git commit -m "cover footer on even pages; explicit header/footer distance; native odd/even setting"
```

---

### Task 3: Schema-ordered OOXML helpers and an order checker

**Files:**
- Modify: `template_build/src/tme_template/oxml_helpers.py`
- Create: `template_build/tests/schema_order.py` (test helper, not a test)
- Test: `template_build/tests/test_schema_order.py` (new)

**Interfaces:**
- Produces (tests): `schema_order.order_violations(root_element) -> list[str]` and `schema_order.document_violations(doc) -> list[str]`, used again in Task 7.
- `oxml_helpers` loses `apply_red_left_rule`, `apply_pullquote_rules`, `set_explicit_tbl_grid` (all dead; verify with grep first). `force_table_full_width` no longer writes `w:tblLayout`; callers already set `table.autofit = False`, which writes it natively.

- [ ] **Step 1: Write the checker helper**

`template_build/tests/schema_order.py`:

```python
"""Walk every w:pPr, w:tblPr and w:tcPr under an element and report children
that are out of ECMA-376 order. The sequences are the ones python-docx uses
internally (docx/oxml/text/parfmt.py and docx/oxml/table.py, 1.2.0)."""
from docx.oxml.ns import qn

PPR_SEQ = (
    "w:pStyle", "w:keepNext", "w:keepLines", "w:pageBreakBefore", "w:framePr",
    "w:widowControl", "w:numPr", "w:suppressLineNumbers", "w:pBdr", "w:shd",
    "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap",
    "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN",
    "w:bidi", "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind",
    "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc",
    "w:textDirection", "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl",
    "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange",
)
TBLPR_SEQ = (
    "w:tblStyle", "w:tblpPr", "w:tblOverlap", "w:bidiVisual",
    "w:tblStyleRowBandSize", "w:tblStyleColBandSize", "w:tblW", "w:jc",
    "w:tblCellSpacing", "w:tblInd", "w:tblBorders", "w:shd", "w:tblLayout",
    "w:tblCellMar", "w:tblLook", "w:tblCaption", "w:tblDescription",
    "w:tblPrChange",
)
TCPR_SEQ = (
    "w:cnfStyle", "w:tcW", "w:gridSpan", "w:hMerge", "w:vMerge", "w:tcBorders",
    "w:shd", "w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign",
    "w:hideMark", "w:headers", "w:cellIns", "w:cellDel", "w:cellMerge",
    "w:tcPrChange",
)
_SEQS = {qn("w:pPr"): PPR_SEQ, qn("w:tblPr"): TBLPR_SEQ, qn("w:tcPr"): TCPR_SEQ}


def _local(tag):
    return tag.split("}")[-1]


def order_violations(root) -> list[str]:
    bad = []
    for tag, seq in _SEQS.items():
        rank = {qn(t): i for i, t in enumerate(seq)}
        for el in root.iter(tag):
            ranks = [rank[c.tag] for c in el if c.tag in rank]
            if ranks != sorted(ranks):
                bad.append(f"{_local(el.tag)}: " + " ".join(_local(c.tag) for c in el))
    return bad


def document_violations(doc) -> list[str]:
    roots = [doc.element.body]
    for s in doc.sections:
        for part in (s.header, s.footer, s.even_page_header, s.even_page_footer):
            if not part.is_linked_to_previous:
                roots.append(part._element)
    out = []
    for r in roots:
        out.extend(order_violations(r))
    return out
```

- [ ] **Step 2: Write the failing tests**

`template_build/tests/test_schema_order.py`:

```python
"""OOXML helpers must insert children in schema order."""
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches

from schema_order import order_violations
from tme_template.oxml_helpers import (
    apply_bottom_rule, apply_top_rule, force_table_full_width,
    remove_cell_borders, set_cell_margins, set_cell_shading,
)


def test_paragraph_border_lands_before_spacing_indent_and_jc():
    doc = Document()
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Inches(0.1)
    p.paragraph_format.left_indent = Inches(1)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    apply_bottom_rule(p, hex_color="BA0C2F", width_pt=1)
    apply_top_rule(p, hex_color="BA0C2F", width_pt=1)
    assert order_violations(doc.element.body) == []


def test_table_and_cell_properties_in_schema_order_whatever_the_call_order():
    doc = Document()
    t = doc.add_table(rows=1, cols=1)
    t.autofit = False
    c = t.cell(0, 0)
    set_cell_margins(c, top=1, bottom=1, left=1, right=1)   # tcMar first on purpose
    set_cell_shading(c, "FFFFFF")                           # shd must land before it
    remove_cell_borders(c)                                  # tcBorders before shd
    c.width = Inches(2)                                     # tcW first of all
    force_table_full_width(t, total_width_inches=8.5)
    assert order_violations(doc.element.body) == []
    tblPr = t._tbl.tblPr
    assert tblPr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblLayout") is not None
```

- [ ] **Step 3: Run to verify failure**

Run: `cd template_build && python3 -m pytest tests/test_schema_order.py -q`
Expected: both FAIL with listed violations (pBdr after spacing/ind/jc; tblW etc. after tblLook; shd after tcMar).

- [ ] **Step 4: Rewrite the helpers**

In `oxml_helpers.py`, replace the file contents up to and including `set_cell_margins` and `force_table_full_width` with the following, keeping `add_section_break_next_page` and `add_continuous_section_break` as they are and deleting `apply_red_left_rule`, `apply_pullquote_rules`, `set_different_odd_even_pages`, `set_different_first_page` and `set_explicit_tbl_grid`:

```python
"""Low-level OOXML helpers for operations python-docx doesn't cover.

Every insert goes through BaseOxmlElement.insert_element_before with the
element's schema successors, so Word, LibreOffice and validators all read the
same thing. The successor tuples are slices of python-docx's own tag
sequences (docx/oxml/text/parfmt.py and docx/oxml/table.py).
"""
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Successors of w:pBdr inside w:pPr.
_PPR_AFTER_PBDR = (
    "w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap",
    "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN",
    "w:bidi", "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind",
    "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc",
    "w:textDirection", "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl",
    "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange",
)
# Order of sides inside w:pBdr.
_BORDER_SEQ = ("w:top", "w:left", "w:bottom", "w:right", "w:between", "w:bar")
# Full w:tcPr and w:tblPr sequences; successors are computed by slicing.
_TCPR_SEQ = (
    "w:cnfStyle", "w:tcW", "w:gridSpan", "w:hMerge", "w:vMerge", "w:tcBorders",
    "w:shd", "w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign",
    "w:hideMark", "w:headers", "w:cellIns", "w:cellDel", "w:cellMerge",
    "w:tcPrChange",
)
_TBLPR_SEQ = (
    "w:tblStyle", "w:tblpPr", "w:tblOverlap", "w:bidiVisual",
    "w:tblStyleRowBandSize", "w:tblStyleColBandSize", "w:tblW", "w:jc",
    "w:tblCellSpacing", "w:tblInd", "w:tblBorders", "w:shd", "w:tblLayout",
    "w:tblCellMar", "w:tblLook", "w:tblCaption", "w:tblDescription",
    "w:tblPrChange",
)


def _after(seq, tag):
    return seq[seq.index(tag) + 1:]


def _get_or_insert(parent, tag, seq):
    """Return parent/<tag>, creating it in schema position if absent."""
    el = parent.find(qn(tag))
    if el is None:
        el = OxmlElement(tag)
        parent.insert_element_before(el, *_after(seq, tag))
    return el


def _replace(parent, tag, seq):
    """Remove any existing parent/<tag> and insert a fresh one in schema position."""
    existing = parent.find(qn(tag))
    if existing is not None:
        parent.remove(existing)
    el = OxmlElement(tag)
    parent.insert_element_before(el, *_after(seq, tag))
    return el


def set_cell_shading(cell, fill_hex: str) -> None:
    """Set a table cell's fill color. fill_hex is 6 hex chars, no leading #."""
    shd = _get_or_insert(cell._tc.get_or_add_tcPr(), "w:shd", _TCPR_SEQ)
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex)


def remove_cell_borders(cell) -> None:
    """Remove all four borders from a table cell."""
    tcBorders = _get_or_insert(cell._tc.get_or_add_tcPr(), "w:tcBorders", _TCPR_SEQ)
    for side in ("top", "left", "bottom", "right"):
        side_el = tcBorders.find(qn(f"w:{side}"))
        if side_el is None:
            side_el = OxmlElement(f"w:{side}")
            tcBorders.append(side_el)   # top, left, bottom, right is schema order
        side_el.set(qn("w:val"), "nil")
        side_el.set(qn("w:sz"), "0")
        side_el.set(qn("w:color"), "auto")


def set_cell_margins(cell, *, top=0, bottom=0, left=80, right=80):
    """Set cell internal margins (twentieths of a point — Word's tcMar units)."""
    tcMar = _replace(cell._tc.get_or_add_tcPr(), "w:tcMar", _TCPR_SEQ)
    for side, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        tcMar.append(el)


def _ensure_pBdr(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = pPr.find(qn("w:pBdr"))
    if pBdr is None:
        pBdr = OxmlElement("w:pBdr")
        pPr.insert_element_before(pBdr, *_PPR_AFTER_PBDR)
    return pBdr


def _set_border(pBdr, side: str, hex_color: str, size_eighths_pt: int):
    """side ∈ {'top','left','bottom','right'}. size is in eighths of a point."""
    el = pBdr.find(qn(f"w:{side}"))
    if el is None:
        el = OxmlElement(f"w:{side}")
        pBdr.insert_element_before(el, *_after(_BORDER_SEQ, f"w:{side}"))
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(size_eighths_pt))
    el.set(qn("w:space"), "4")
    el.set(qn("w:color"), hex_color)


def apply_bottom_rule(paragraph, hex_color: str, width_pt: int = 1) -> None:
    """Colored bottom border on a paragraph (horizontal rule effect)."""
    _set_border(_ensure_pBdr(paragraph), "bottom", hex_color, width_pt * 8)


def apply_top_rule(paragraph, hex_color: str, width_pt: int = 1) -> None:
    """Colored top border on a paragraph (e.g., footer separator)."""
    _set_border(_ensure_pBdr(paragraph), "top", hex_color, width_pt * 8)


def force_table_full_width(table, total_width_inches: float = 8.5,
                           left_indent_inches: float = 0.0):
    """Render a table at exactly the given width with a given left indent and
    zero default cell margins. Needed because python-docx sizes a new table to
    the body width, and treats a zero margin as unset (1") when computing it,
    so tables in zero-margin sections come out 6.5" wide.

    Callers set `table.autofit = False` themselves; that writes w:tblLayout
    type=fixed natively, so column widths are honored."""
    tblPr = table._tbl.tblPr
    tblW = _replace(tblPr, "w:tblW", _TBLPR_SEQ)
    tblW.set(qn("w:w"), str(int(total_width_inches * 1440)))
    tblW.set(qn("w:type"), "dxa")
    tblInd = _replace(tblPr, "w:tblInd", _TBLPR_SEQ)
    tblInd.set(qn("w:w"), str(int(left_indent_inches * 1440)))
    tblInd.set(qn("w:type"), "dxa")
    tblCellMar = _replace(tblPr, "w:tblCellMar", _TBLPR_SEQ)
    for side in ("top", "left", "bottom", "right"):
        m = OxmlElement(f"w:{side}")
        m.set(qn("w:w"), "0")
        m.set(qn("w:type"), "dxa")
        tblCellMar.append(m)
```

Before deleting, run `grep -rn "apply_red_left_rule\|apply_pullquote_rules\|set_explicit_tbl_grid" template_build tme_editor_app moore_build`. Expected: only definitions in oxml_helpers.py and the comment in styles.py (fixed in Task 5). If a caller exists, keep that function and tell the reviewer.

- [ ] **Step 5: Run the suite**

Run: `cd template_build && python3 -m pytest tests -q`
Expected: all pass. (`force_table_full_width` is called in masthead, tagline and cover_footer; each sets autofit False first, so tblLayout still appears.)

- [ ] **Step 6: Commit**

```bash
git add template_build/src/tme_template/oxml_helpers.py template_build/tests/schema_order.py template_build/tests/test_schema_order.py
git commit -m "oxml helpers: insert in schema order; drop dead rule and grid helpers"
```

---

### Task 4: Cell widths that agree with the grid; shared constants; shared red run; small nits

**Files:**
- Create: `template_build/src/tme_template/runs.py`
- Modify: `template_build/src/tme_template/masthead.py`
- Modify: `template_build/src/tme_template/tagline.py`
- Modify: `template_build/src/tme_template/cover_page.py`
- Modify: `template_build/src/tme_template/front_matter.py`
- Modify: `template_build/src/build_template.py` (one call site: `add_editorial_staff_page` loses its unused `issue` parameter)
- Test: `template_build/tests/test_cell_widths.py` (new)

**Interfaces:**
- Produces: `runs.add_red_run(paragraph, text, *, size_pt, bold=False, name="Arial")`.
- `add_editorial_staff_page(doc, roster)` (was `(doc, issue, roster)`).
- `AuthorEntry.role` stays in the dataclass (callers pass it) but is documented as unused by the cover layout.

- [ ] **Step 1: Write the failing tests**

```python
"""Table widths: tcW (Word) and gridCol (LibreOffice) must agree; no blank DOI line."""
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Inches

from tme_template.cover_page import AuthorEntry, CoverData, add_research_article_cover
from tme_template.layout import FULL_BLEED_WIDTH, MASTHEAD_LEFT_WIDTH, MASTHEAD_RIGHT_WIDTH
from tme_template.masthead import MastheadData, add_masthead
from tme_template.styles import register_title_style
from tme_template.tagline import add_tagline_strip

LOGO = str(Path(__file__).resolve().parents[2] / "assets" / "tme-logo.jpg")


def _grid(table):
    return [int(c.get(qn("w:w"))) for c in table._tbl.tblGrid.findall(qn("w:gridCol"))]


def _tcw(cell):
    return int(cell._tc.tcPr.find(qn("w:tcW")).get(qn("w:w")))


def _masthead(doi="doi.org/10.1/x"):
    return MastheadData(article_type="RESEARCH ARTICLE", volume=34, number=1, year=2026,
                        pages="1–24", doi=doi, issn_print="1062-9017",
                        issn_online="2331-4451", logo_path=LOGO)


def test_masthead_cells_match_grid_and_layout_constants():
    doc = Document()
    add_masthead(doc, _masthead())
    t = doc.tables[0]
    assert _grid(t) == [MASTHEAD_LEFT_WIDTH.twips, MASTHEAD_RIGHT_WIDTH.twips]
    assert [_tcw(c) for c in t.rows[0].cells] == _grid(t)


def test_masthead_without_doi_has_no_blank_line():
    doc = Document()
    add_masthead(doc, _masthead(doi=None))
    right = doc.tables[0].cell(0, 1)
    assert all(p.text.strip() for p in right.paragraphs)


def test_tagline_cell_is_full_bleed():
    doc = Document()
    add_tagline_strip(doc)
    t = doc.tables[0]
    assert _grid(t) == [FULL_BLEED_WIDTH.twips]
    assert _tcw(t.cell(0, 0)) == FULL_BLEED_WIDTH.twips


def test_author_card_widths_split_evenly_without_table_grid_style():
    doc = Document()
    register_title_style(doc)
    authors = [AuthorEntry(name=f"A{i}", affiliation_num=1, role=None, bio="b", headshot_path=None)
               for i in range(4)]
    add_research_article_cover(doc, CoverData(
        title="T", authors=authors, affiliations=["X"], dates={"Received": "d"},
        abstract="abs", keywords=["k"]))
    card = doc.tables[0]
    expected = Inches(7.5 / 4).twips
    assert _grid(card) == [expected] * 4
    assert [_tcw(c) for c in card.rows[0].cells] == [expected] * 4
    assert card.style is None or card.style.name != "Table Grid"
```

- [ ] **Step 2: Run to verify failure**

Run: `cd template_build && python3 -m pytest tests/test_cell_widths.py -q`
Expected: FAIL (masthead tcW 3.25" vs grid; DOI blank paragraph; author card uses Table Grid).

- [ ] **Step 3: runs.py**

```python
"""Run helpers shared by the cover builders."""
from docx.shared import Pt, RGBColor

from tme_template.colors import UGA_RED


def add_red_run(paragraph, text: str, *, size_pt: float, bold: bool = False, name: str = "Arial"):
    """Append a UGA-red run (Arial by default) and return it."""
    r = paragraph.add_run(text)
    r.font.name = name
    r.font.size = Pt(size_pt)
    r.font.bold = bold
    r.font.color.rgb = RGBColor.from_string(UGA_RED)
    return r
```

- [ ] **Step 4: masthead.py**

Replace the imports and `add_masthead` body up to the cell loop with:

```python
from docx.enum.table import WD_ALIGN_VERTICAL, WD_ROW_HEIGHT_RULE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

from tme_template.colors import BLACK, UGA_RED
from tme_template.layout import BLEED_IN, MASTHEAD_LEFT_WIDTH, MASTHEAD_RIGHT_WIDTH, PAGE_WIDTH_IN
from tme_template.oxml_helpers import (
    force_table_full_width,
    remove_cell_borders,
    set_cell_margins,
    set_cell_shading,
)
```

(The logo loading itself is unchanged in this task; Task 6 routes it through `tme_template.images`.)

```python
def add_masthead(doc, data: MastheadData) -> None:
    """Append the masthead (2-col table) to a document body."""
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    # Widths go on both the grid (gridCol, which LibreOffice reads) and the
    # cells (tcW, which Word reads); python-docx's column.width writes only
    # the former. The bleed is explained in layout.py.
    for col, width in zip(table.columns, (MASTHEAD_LEFT_WIDTH, MASTHEAD_RIGHT_WIDTH)):
        col.width = width
        for cell in col.cells:
            cell.width = width
    row = table.rows[0]
    row.height = Pt(75)
    row.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST

    force_table_full_width(table, total_width_inches=PAGE_WIDTH_IN + BLEED_IN)
```

Delete the local `TOTAL_WIDTH`/`BLEED_INCHES` constants and the old `table.columns[i].width` lines. At the bottom, replace

```python
    _add_line(data.doi or "", size_pt=10.5)
```
with
```python
    if data.doi:
        _add_line(data.doi, size_pt=10.5)
```

- [ ] **Step 5: tagline.py**

Replace the module header through the cell setup with:

```python
"""Generate the light-gray tagline strip that sits beneath the masthead."""
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

from tme_template.colors import LIGHT_PANEL_GRAY, META
from tme_template.layout import BLEED_IN, FULL_BLEED_WIDTH, PAGE_WIDTH_IN
from tme_template.oxml_helpers import (
    force_table_full_width,
    remove_cell_borders,
    set_cell_margins,
    set_cell_shading,
)
from tme_template.runs import add_red_run


TAGLINE = "Cultivating scholarly discourse in mathematics education since 1990"
META_LINE = ("Published by the Mathematics Education Student Association"
             "  ·  University of Georgia  ·  Peer Reviewed  ·  Open Access")
# U+25CA lozenge: in the WGL4 set that both Georgia and Arial cover. The
# filled diamond U+25C6 used before is not, so Word substituted a symbol
# font that differs between Mac and Windows.
ORNAMENT = "◊"


def _gray_run(paragraph, text: str, *, name="Georgia", size_pt=11.0, italic=False):
    r = paragraph.add_run(text)
    r.font.name = name
    r.font.size = Pt(size_pt)
    r.font.italic = italic
    r.font.color.rgb = RGBColor.from_string(META)
    return r


def add_tagline_strip(doc) -> None:
    table = doc.add_table(rows=1, cols=1)
    table.autofit = False
    table.columns[0].width = FULL_BLEED_WIDTH
    cell = table.cell(0, 0)
    cell.width = FULL_BLEED_WIDTH     # tcW; column.width only writes the grid
    remove_cell_borders(cell)
    set_cell_shading(cell, LIGHT_PANEL_GRAY)
    force_table_full_width(table, total_width_inches=PAGE_WIDTH_IN + BLEED_IN)
    set_cell_margins(cell, top=80, bottom=80, left=160, right=160)
```

Delete the manual `tcW` block and its comment, delete `_red_run`, and replace the two `_red_run(p1, "◆ ", size_pt=9.5)` / `_red_run(p1, " ◆", size_pt=9.5)` calls with `add_red_run(p1, ORNAMENT + " ", size_pt=9.5)` and `add_red_run(p1, " " + ORNAMENT, size_pt=9.5)`. Remove the now-unused `OxmlElement`, `qn`, `Inches`, `UGA_RED` imports.

- [ ] **Step 6: cover_page.py**

- Replace `from typing import List, Optional, Dict` line's companion `from dataclasses import dataclass, field` with `from dataclasses import dataclass` (`field` unused).
- Add `from tme_template.runs import add_red_run`; delete `_red_label` and replace its two calls with `add_red_run(ab_lbl, "ABOUT THE AUTHORS", size_pt=9, bold=True)` and `add_red_run(lbl, "ABSTRACT", size_pt=9, bold=True)`.
- Document the unused field: change `role: Optional[str]` to `role: Optional[str]  # accepted for compatibility; the cover layout does not render it`.
- Replace the author-card table setup (from `n = len(data.authors)` through the manual `tcW` block inside the loop) with:

```python
    # Author block — one cell per author
    n = len(data.authors)
    col_width = Inches(7.5 / n)
    tbl = doc.add_table(rows=1, cols=n)
    tbl.autofit = False
    for col in tbl.columns:
        col.width = col_width
        for cell in col.cells:
            cell.width = col_width

    # Keep author row from breaking across pages
    row = tbl.rows[0]
    trPr = row._tr.get_or_add_trPr()
    cantSplit = OxmlElement('w:cantSplit')
    trPr.append(cantSplit)

    for col_idx, a in enumerate(data.authors):
        cell = tbl.cell(0, col_idx)
        remove_cell_borders(cell)
        set_cell_margins(cell, top=0, bottom=0, left=80, right=80)
```

(no `tbl.style = "Table Grid"`; the default style has no borders to remove, and the explicit `remove_cell_borders` stays as belt-and-braces). Remove the `qn` import if nothing else uses it.

- [ ] **Step 7: front_matter.py**

- `from dataclasses import dataclass` (drop `field`); add `from docx.enum.table import WD_ROW_HEIGHT_RULE`; add `from tme_template.runs import add_red_run`; delete `_red_run`, `_section_label`, `_role_group`; replace `_red_run(p, text, size_pt=N)` calls with `add_red_run(p, text, size_pt=N, bold=True)` (there are three: in `_section_label_in_cell`, `add_issue_cover_page`, `add_formal_title_page`).
- In `add_issue_cover_page`, replace the `trPr`/`trHeight` block with:

```python
    row = table.rows[0]
    row.height = Inches(9)   # fills the page at the 0.3" margins the template uses
    row.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
```
and set `table.cell(0, 0).width = Inches(6.5)` right after `table.columns[0].width = Inches(6.5)`.
- In `add_editorial_staff_page`, change the signature to `def add_editorial_staff_page(doc, roster: StaffRoster) -> None:` and after the two `columns[i].width = Inches(3.25)` lines add `for cell in table.rows[0].cells: cell.width = Inches(3.25)`.
- In `build_template.py`, change the call to `add_editorial_staff_page(doc, StaffRoster(`.
- Remove unused imports (`OxmlElement`, `qn`) if nothing else in the module uses them.

- [ ] **Step 8: Run the suite**

Run: `cd template_build && python3 -m pytest tests -q`
Expected: all pass. The schema-order test from Task 3 still passes.

- [ ] **Step 9: Commit**

```bash
git add template_build/src/tme_template/runs.py template_build/src/tme_template/masthead.py template_build/src/tme_template/tagline.py template_build/src/tme_template/cover_page.py template_build/src/tme_template/front_matter.py template_build/src/build_template.py template_build/tests/test_cell_widths.py
git commit -m "cover tables: write tcW with gridCol; shared layout constants and red run; drop blank DOI line"
```

---

### Task 5: Styles — drop the H1 indent, outline levels, gallery visibility, table text style

**Files:**
- Modify: `template_build/src/tme_template/styles.py`
- Test: `template_build/tests/test_styles_updates.py` (append)

**Interfaces:**
- Produces: paragraph style `"TME Table Text"` (Georgia 10pt, single spacing, 2pt after). The editor app's fixup assigns it to content-table cells and creates it itself if missing, so no ordering dependency.
- `TME H1`, `TME H2`, `TME H3` carry `w:outlineLvl` 0, 1, 2.

- [ ] **Step 1: Append the failing tests**

```python
from docx.oxml.ns import qn


def _outline(style):
    el = style.element.pPr.find(qn("w:outlineLvl")) if style.element.pPr is not None else None
    return None if el is None else el.get(qn("w:val"))


def test_headings_carry_outline_levels():
    doc = Document()
    register_heading_styles(doc)
    assert [_outline(doc.styles[n]) for n in ("TME H1", "TME H2", "TME H3")] == ["0", "1", "2"]


def test_h1_has_no_left_indent():
    doc = Document()
    register_heading_styles(doc)
    assert doc.styles["TME H1"].paragraph_format.left_indent is None


def test_tme_styles_show_in_the_gallery():
    doc = Document()
    register_body_style(doc)
    register_heading_styles(doc)
    register_remaining_styles(doc)
    for name in ("TME Body", "TME H1", "TME Figure Caption", "TME Reference", "List Paragraph"):
        assert doc.styles[name].quick_style is True, name


def test_table_text_style_is_registered():
    doc = Document()
    register_remaining_styles(doc)
    tt = doc.styles["TME Table Text"]
    assert tt.font.name == "Georgia" and tt.font.size == Pt(10)
    assert tt.paragraph_format.line_spacing == 1.0
```

Add `register_body_style` to the existing import from `tme_template.styles`.

- [ ] **Step 2: Run to verify failure**

Run: `cd template_build && python3 -m pytest tests/test_styles_updates.py -q`
Expected: the four new tests FAIL.

- [ ] **Step 3: Edit styles.py**

Replace `_get_or_add_paragraph_style` and `register_heading_styles` with:

```python
from docx.oxml.ns import qn


def _get_or_add_paragraph_style(doc, name: str):
    """Return the style by name (adding a paragraph style if absent) and make
    sure it shows in Word's Styles gallery."""
    style = doc.styles[name] if name in doc.styles else doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    style.quick_style = True
    return style


def _set_outline_level(style, level: int) -> None:
    """Outline level makes Word's Navigation pane, TOC generation and PDF
    bookmarks see the heading; without it the document reads as flat."""
    el = style.element.get_or_add_pPr().get_or_add_outlineLvl()
    el.set(qn("w:val"), str(level))
```

In `register_heading_styles`: replace the docstring with `"""H1–H3: Georgia, bold, tight spacing, kept with the next paragraph."""`, delete the `h1.paragraph_format.left_indent = Pt(10)` line, and add `_set_outline_level(h1, 0)`, `_set_outline_level(h2, 1)`, `_set_outline_level(h3, 2)` after each heading's block.

In `register_remaining_styles`: delete the `TME Pullquote` comment line `# Horizontal rules above/below applied at element time — see oxml_helpers.` (the helper is gone) and add before the `List Paragraph` block:

```python
    # Content-table cells. The editor app assigns this to every paragraph in a
    # pasted table so cells render in Georgia instead of the theme font.
    tt = _get_or_add_paragraph_style(doc, "TME Table Text")
    tt.font.name = "Georgia"
    tt.font.size = Pt(10)
    tt.paragraph_format.line_spacing = 1.0
    tt.paragraph_format.space_before = Pt(0)
    tt.paragraph_format.space_after = Pt(2)
```

- [ ] **Step 4: Run the suite**

Run: `cd template_build && python3 -m pytest tests -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add template_build/src/tme_template/styles.py template_build/tests/test_styles_updates.py
git commit -m "styles: outline levels on headings, gallery visibility, table text style, no H1 indent"
```

---

### Task 6: Builders — explicit page flow, one image policy, section aliasing note

**Files:**
- Create: `template_build/src/tme_template/images.py`
- Modify: `template_build/src/tme_template/masthead.py` (logo through `open_image_as_rgb_stream`, no try/except)
- Modify: `template_build/src/tme_template/front_matter.py` (use `images.py`; no try/except; title-page spacer as exact line height)
- Modify: `template_build/src/tme_template/oxml_helpers.py` (docstring on the two section-break helpers)
- Modify: `template_build/src/build_template.py` (`build(out_path=OUTPUT)`, page break after the issue cover, drop redundant page-size lines)
- Test: `template_build/tests/test_builders.py` (new)

**Interfaces:**
- Produces: `images.open_image_as_rgb_stream(path) -> io.BytesIO` (raises `FileNotFoundError` for a missing file, `PIL.UnidentifiedImageError` for a non-image).
- Produces: `build_template.build(out_path: Path = OUTPUT) -> Path`.

- [ ] **Step 1: Write the failing tests**

```python
"""Builders fail loudly on missing images and separate pages explicitly."""
from pathlib import Path

import pytest
from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Pt

from tme_template.front_matter import IssueInfo, add_formal_title_page, add_issue_cover_page
from tme_template.masthead import MastheadData, add_masthead

LOGO = str(Path(__file__).resolve().parents[2] / "assets" / "tme-logo.jpg")
LOGO_P = str(Path(__file__).resolve().parents[2] / "assets" / "tme-logo-portrait.jpg")


def test_masthead_with_missing_logo_raises():
    doc = Document()
    with pytest.raises(FileNotFoundError):
        add_masthead(doc, MastheadData(article_type="X", volume=1, number=1, year=2026, pages=None,
                                       doi=None, issn_print="1", issn_online="2",
                                       logo_path="/nonexistent/logo.jpg"))


def test_issue_cover_with_missing_portrait_raises():
    doc = Document()
    with pytest.raises(FileNotFoundError):
        add_issue_cover_page(doc, IssueInfo(volume=1, number=1, year=2026, season="Spring",
                                            cover_artist=None, portrait_logo_path="/nonexistent.jpg"))


def test_title_page_spacer_is_an_exact_line_height_not_space_before():
    doc = Document()
    add_formal_title_page(doc, IssueInfo(volume=1, number=1, year=2026, season="Spring",
                                         cover_artist=None, portrait_logo_path=LOGO_P))
    spacer = doc.paragraphs[0]
    assert spacer.paragraph_format.line_spacing == Pt(120)
    assert spacer.paragraph_format.line_spacing_rule == WD_LINE_SPACING.EXACTLY
    assert spacer.paragraph_format.space_before is None
```

- [ ] **Step 2: Run to verify failure**

Run: `cd template_build && python3 -m pytest tests/test_builders.py -q`
Expected: the two "raises" tests FAIL (the builders print a warning instead), the spacer test FAILS on `line_spacing`.

- [ ] **Step 3: images.py**

```python
"""Image normalization for python-docx picture insertion."""
import io

from PIL import Image


def open_image_as_rgb_stream(path: str) -> io.BytesIO:
    """Open an image and return it as an in-memory sRGB JPEG stream.

    python-docx cannot embed CMYK JPEGs or palette PNGs with transparency
    reliably, so every logo goes through this. Raises FileNotFoundError for a
    missing file and PIL.UnidentifiedImageError for a non-image; library code
    does not swallow those — the caller decides what a missing logo means.
    """
    with Image.open(path) as img:
        rgb = img.convert("RGB")
    buf = io.BytesIO()
    rgb.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    return buf
```

- [ ] **Step 4: Use it in masthead.py and front_matter.py**

masthead.py: replace the `try: ... except FileNotFoundError: ... print(...)` block around the logo with

```python
    left.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = left.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(open_image_as_rgb_stream(data.logo_path), width=Inches(3.0))
```

front_matter.py: delete `_open_image_as_rgb_stream` and the `import io`; add `from tme_template.images import open_image_as_rgb_stream`; replace the `try/except` around the portrait logo with

```python
    p_logo.add_run().add_picture(open_image_as_rgb_stream(issue.portrait_logo_path), height=Inches(4.0))
```

In `add_formal_title_page`, replace

```python
    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_before = Pt(120)
```
with
```python
    # An exact 120pt line, not space-before: Word suppresses space-before at
    # the top of a page after a hard break, and build_template now starts this
    # page with one.
    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    p_spacer.paragraph_format.line_spacing = Pt(120)
```
and add `from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING`.

- [ ] **Step 5: build_template.py**

- Signature: `def build(out_path: Path = OUTPUT) -> Path:` and `doc.save(str(out_path)); return out_path`.
- After `add_issue_cover_page(doc, issue)` replace the comment line with:

```python
    # Explicit page break: the cover table is 9" at-least and the title page
    # opened with a 120pt spacer, so the pages used to separate only by
    # overflow arithmetic.
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
```
and import `from docx.enum.text import WD_BREAK`.
- Delete the four `*.page_width = Inches(8.5)` / `*.page_height = Inches(11)` pairs on `ed_masthead_section`, `ed_body_section`, `masthead_section`, `cover_body_section` (`add_section` clones the previous sectPr, so they inherit Letter).
- Add at the top of `build()`:

```python
    # python-docx caveat: doc.add_section() reuses the body's sentinel sectPr
    # for the NEW section and clones it to close the old one, so a Section
    # object fetched earlier silently points at the newest section afterwards.
    # Every mutation of a section below happens before the next break is
    # added; keep it that way, or re-fetch via doc.sections[i].
```

- [ ] **Step 6: Docstrings on the section helpers in oxml_helpers.py**

Append to both `add_section_break_next_page` and `add_continuous_section_break` docstrings:
`Note: python-docx reuses the body sentinel sectPr, so Section objects obtained before this call now refer to the new section; finish configuring a section before adding the next break.`

- [ ] **Step 7: Run the suite**

Run: `cd template_build && python3 -m pytest tests -q`
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add template_build/src/tme_template/images.py template_build/src/tme_template/masthead.py template_build/src/tme_template/front_matter.py template_build/src/tme_template/oxml_helpers.py template_build/src/build_template.py template_build/tests/test_builders.py
git commit -m "builders: explicit page break, one image policy that raises, section aliasing note"
```

---

### Task 7: Golden build test and test cleanups

**Files:**
- Test: `template_build/tests/test_build_template.py` (new)
- Modify: `template_build/tests/test_headers_footers_update.py:17` (PAGE assertion)
- Modify: `template_build/tests/test_colors.py` (replace self-equality asserts)
- Modify: `template_build/pyproject.toml` (`python-docx>=1.1`, version `1.2.0`)

**Interfaces:**
- Consumes: `build(out_path)` from Task 6, `document_violations` from Task 3.

- [ ] **Step 1: Write the golden build test**

```python
"""Build the whole template into tmp_path and check its structure."""
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import build_template  # noqa: E402
from schema_order import document_violations  # noqa: E402


def _footer_types(section):
    return sorted(el.get(qn("w:type")) for el in section._sectPr.findall(qn("w:footerReference")))


def test_build_has_six_sections_both_cover_footers_and_schema_order(tmp_path):
    out = build_template.build(tmp_path / "template.docx")
    doc = Document(str(out))

    # [0] issue cover + title page, [1] editorial masthead, [2] editorial body,
    # [3] article masthead (zero margins), [4] article cover body, [5] body pages
    assert len(doc.sections) == 6
    assert _footer_types(doc.sections[3]) == ["default", "even"]   # was ["default"] only
    assert doc.sections[5].header.is_linked_to_previous is False
    assert doc.sections[5].even_page_header.is_linked_to_previous is False
    assert document_violations(doc) == [], document_violations(doc)[:5]
```

- [ ] **Step 2: Run to verify it fails or passes honestly**

Run: `cd template_build && python3 -m pytest tests/test_build_template.py -q`
Expected: PASS if Tasks 2–6 landed; if `document_violations` lists anything, fix the helper that produced it (that is the point of the checker) and rerun.

- [ ] **Step 3: Fix the weak assertions**

In `test_headers_footers_update.py`, replace `_footer_has_page_field` with:

```python
def _footer_has_page_field(section):
    """The footer must carry a real PAGE field instruction, not the letters."""
    instr = section.footer._element.findall(".//" + qn("w:instrText"))
    return any((i.text or "").strip() == "PAGE" for i in instr)
```
and add `from docx.oxml.ns import qn`.

In `test_colors.py`, replace any `assert X == X` style asserts with a format check:

```python
import re
from tme_template import colors

def test_palette_values_are_six_hex_digits():
    names = [n for n in dir(colors) if n.isupper()]
    assert names
    for n in names:
        assert re.fullmatch(r"[0-9A-Fa-f]{6}", getattr(colors, n)), n
```
(keep any existing test that checks a specific value against a documented spec.)

- [ ] **Step 4: pyproject.toml**

`version = "1.2.0"`, `"python-docx>=1.1"` (the helpers rely on `insert_element_before`, `quick_style`, `header_distance`, `odd_and_even_pages_header_footer`, all present in 1.1+).

- [ ] **Step 5: Run the suite**

Run: `cd template_build && python3 -m pytest tests -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add template_build/tests/test_build_template.py template_build/tests/test_headers_footers_update.py template_build/tests/test_colors.py template_build/pyproject.toml
git commit -m "template tests: golden build with schema-order check; real PAGE field and palette asserts"
```

---

## Self-review notes

- Section count verified against the current builder on 7 Oct: six sections, article masthead at index 3 with a default-only footer.
- Spec coverage: T1, T2, T10 → Task 1; T3, T4 (documented, not changed, per owner) → Task 2; T5 → Task 3; T6 and nits (red run, constants, Table Grid, trHeight, DOI line, height rule, diamond glyph, dead code) → Task 4; T7, T8, T9 → Task 5 (helpers deleted in Task 3); T11, T12, T13 and the page-size nit → Task 6; T15 → Task 7. T14 is intentionally not implemented (owner decision); the compat-mode dependency is documented in `layout.py`.
- The lozenge glyph (U+25CA) replaces the filled diamond (U+25C6) in the tagline; the owner should look at it once in Word and can switch `ORNAMENT` to any WGL4 glyph.
