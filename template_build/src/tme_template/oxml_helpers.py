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
        # w:pBdr has no python-docx element class, so it lacks
        # insert_element_before; place the side before its first successor.
        successor = next(
            (c for t in _after(_BORDER_SEQ, f"w:{side}") for c in pBdr.findall(qn(t))),
            None,
        )
        if successor is None:
            pBdr.append(el)
        else:
            successor.addprevious(el)
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


def add_section_break_next_page(doc):
    """Add a next-page section break and return the new Section object.

    Use this to start a new section on a fresh page so each section can
    have independent header/footer settings.

    Note: python-docx reuses the body sentinel sectPr, so Section objects obtained
    before this call now refer to the new section; finish configuring a section
    before adding the next break.
    """
    from docx.enum.section import WD_SECTION
    return doc.add_section(WD_SECTION.NEW_PAGE)


def add_continuous_section_break(doc):
    """Add a continuous section break (no page break) and return the new section.

    Note: python-docx reuses the body sentinel sectPr, so Section objects obtained
    before this call now refer to the new section; finish configuring a section
    before adding the next break.
    """
    from docx.enum.section import WD_SECTION
    return doc.add_section(WD_SECTION.CONTINUOUS)


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
