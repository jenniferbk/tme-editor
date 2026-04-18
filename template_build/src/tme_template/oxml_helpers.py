"""Low-level OOXML helpers for operations python-docx doesn't cover."""
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def set_cell_shading(cell, fill_hex: str) -> None:
    """Set a table cell's fill color.

    fill_hex is a 6-char hex string without leading #.
    """
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tcPr.append(shd)
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex)


def remove_cell_borders(cell) -> None:
    """Remove all four borders from a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = tcPr.find(qn("w:tcBorders"))
    if tcBorders is None:
        tcBorders = OxmlElement("w:tcBorders")
        tcPr.append(tcBorders)
    for side in ("top", "left", "bottom", "right"):
        side_el = tcBorders.find(qn(f"w:{side}"))
        if side_el is None:
            side_el = OxmlElement(f"w:{side}")
            tcBorders.append(side_el)
        side_el.set(qn("w:val"), "nil")
        side_el.set(qn("w:sz"), "0")
        side_el.set(qn("w:color"), "auto")


def set_different_odd_even_pages(doc) -> None:
    """Enable 'Different Odd & Even Pages' at document level."""
    settings = doc.settings.element
    existing = settings.find(qn("w:evenAndOddHeaders"))
    if existing is None:
        el = OxmlElement("w:evenAndOddHeaders")
        settings.append(el)


def set_different_first_page(section, value: bool) -> None:
    """Enable 'Different First Page' on a section."""
    section.different_first_page_header_footer = value


def _ensure_pBdr(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = pPr.find(qn("w:pBdr"))
    if pBdr is None:
        pBdr = OxmlElement("w:pBdr")
        pPr.append(pBdr)
    return pBdr


def _set_border(pBdr, side: str, hex_color: str, size_eighths_pt: int):
    """side ∈ {'top','left','bottom','right'}. size is in eighths of a point."""
    el = pBdr.find(qn(f"w:{side}"))
    if el is None:
        el = OxmlElement(f"w:{side}")
        pBdr.append(el)
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(size_eighths_pt))
    el.set(qn("w:space"), "4")
    el.set(qn("w:color"), hex_color)


def apply_red_left_rule(paragraph, hex_color: str, width_pt: int = 3) -> None:
    """Apply a colored left border to a paragraph (e.g., the H1 red rule)."""
    pBdr = _ensure_pBdr(paragraph)
    # sz unit is eighths of a point; 3pt = 24 eighths
    _set_border(pBdr, "left", hex_color, width_pt * 8)


def apply_bottom_rule(paragraph, hex_color: str, width_pt: int = 1) -> None:
    """Apply a colored bottom border to a paragraph (horizontal rule effect)."""
    pBdr = _ensure_pBdr(paragraph)
    _set_border(pBdr, "bottom", hex_color, width_pt * 8)


def apply_top_rule(paragraph, hex_color: str, width_pt: int = 1) -> None:
    """Apply a colored top border to a paragraph (e.g., footer separator)."""
    pBdr = _ensure_pBdr(paragraph)
    _set_border(pBdr, "top", hex_color, width_pt * 8)


def apply_pullquote_rules(paragraph, top_hex: str, bottom_hex: str) -> None:
    """Apply top (thicker) and bottom (thinner) red rules for pullquotes."""
    pBdr = _ensure_pBdr(paragraph)
    _set_border(pBdr, "top", top_hex, 16)     # 2pt = 16 eighths
    _set_border(pBdr, "bottom", bottom_hex, 8) # 1pt = 8 eighths


def set_cell_margins(cell, *, top=0, bottom=0, left=80, right=80):
    """Set cell internal margins (in twentieths of a point — Word's tcMar units)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for side, val in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        tcMar.append(el)
    # Remove existing tcMar if any
    existing = tcPr.find(qn("w:tcMar"))
    if existing is not None:
        tcPr.remove(existing)
    tcPr.append(tcMar)


def add_section_break_next_page(doc):
    """Add a next-page section break and return the new Section object.

    Use this to start a new section on a fresh page so each section can
    have independent header/footer settings.
    """
    from docx.enum.section import WD_SECTION
    return doc.add_section(WD_SECTION.NEW_PAGE)


def add_continuous_section_break(doc):
    """Add a continuous section break (no page break) and return the new section."""
    from docx.enum.section import WD_SECTION
    return doc.add_section(WD_SECTION.CONTINUOUS)


def force_table_full_width(table, total_width_inches: float = 8.5,
                           left_indent_inches: float = 0.0):
    """Force a table to render at exactly the given width with a specified left
    indent and no auto-resize. Required when default Word behavior shrinks tables
    inside zero-margin sections."""
    # Twentieths of a point: 1 inch = 1440 twips
    total_twips = int(total_width_inches * 1440)
    indent_twips = int(left_indent_inches * 1440)
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else None
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr)

    # Set or replace tblW
    existing_tblW = tblPr.find(qn("w:tblW"))
    if existing_tblW is not None:
        tblPr.remove(existing_tblW)
    tblW = OxmlElement("w:tblW")
    tblW.set(qn("w:w"), str(total_twips))
    tblW.set(qn("w:type"), "dxa")
    tblPr.append(tblW)

    # Set tblInd
    existing_tblInd = tblPr.find(qn("w:tblInd"))
    if existing_tblInd is not None:
        tblPr.remove(existing_tblInd)
    tblInd = OxmlElement("w:tblInd")
    tblInd.set(qn("w:w"), str(indent_twips))
    tblInd.set(qn("w:type"), "dxa")
    tblPr.append(tblInd)

    # Set tblLayout to fixed so column widths are honored
    existing_layout = tblPr.find(qn("w:tblLayout"))
    if existing_layout is not None:
        tblPr.remove(existing_layout)
    tblLayout = OxmlElement("w:tblLayout")
    tblLayout.set(qn("w:type"), "fixed")
    tblPr.append(tblLayout)

    # Zero out default cell margins for the table
    existing_tblCellMar = tblPr.find(qn("w:tblCellMar"))
    if existing_tblCellMar is not None:
        tblPr.remove(existing_tblCellMar)
    tblCellMar = OxmlElement("w:tblCellMar")
    for side in ("top", "left", "bottom", "right"):
        m = OxmlElement(f"w:{side}")
        m.set(qn("w:w"), "0")
        m.set(qn("w:type"), "dxa")
        tblCellMar.append(m)
    tblPr.append(tblCellMar)


def set_explicit_tbl_grid(table, col_widths_twips):
    """Replace the tblGrid with exactly these columns (widths in twips).

    When two adjacent tables with no paragraph between them are saved by Word,
    Word can merge them into one table with a unioned grid that contains tiny
    phantom columns at the edges. Rewriting tblGrid and removing gridBefore/
    gridAfter/wBefore/wAfter from every row eliminates those phantoms.
    """
    tbl = table._tbl
    # Replace tblGrid
    existing_grid = tbl.find(qn("w:tblGrid"))
    if existing_grid is not None:
        tbl.remove(existing_grid)
    tblGrid = OxmlElement("w:tblGrid")
    for w in col_widths_twips:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(int(w)))
        tblGrid.append(col)
    # Insert tblGrid immediately after tblPr
    tblPr = tbl.find(qn("w:tblPr"))
    if tblPr is not None:
        tblPr.addnext(tblGrid)
    else:
        tbl.insert(0, tblGrid)

    # Strip gridBefore/gridAfter/wBefore/wAfter from every row
    for tr in tbl.findall(qn("w:tr")):
        trPr = tr.find(qn("w:trPr"))
        if trPr is None:
            continue
        for tag in ("w:gridBefore", "w:gridAfter", "w:wBefore", "w:wAfter"):
            for el in trPr.findall(qn(tag)):
                trPr.remove(el)
