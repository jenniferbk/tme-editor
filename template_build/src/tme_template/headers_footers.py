"""Verso/recto running headers and the static running footer."""
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

from tme_template.oxml_helpers import apply_top_rule


def _clear(header_or_footer):
    for p in list(header_or_footer.paragraphs):
        p._p.getparent().remove(p._p)


def _add_italic_gray_line(container, text: str, align):
    p = container.add_paragraph()
    p.alignment = align
    r = p.add_run(text)
    r.font.name = "Georgia"
    r.font.size = Pt(10.5)
    r.font.italic = True
    r.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
    return p


def set_running_headers(doc, author_cite: str, short_title: str, section=None) -> None:
    """Verso (even): author cite flush left. Recto (odd): short title flush right.

    If *section* is provided, operate only on that section object.
    When None (default), operate on all sections (backward-compatible).
    """
    if section is not None:
        section.header.is_linked_to_previous = False
        section.even_page_header.is_linked_to_previous = False
    sections = [section] if section is not None else doc.sections
    for sec in sections:
        # Recto / odd
        recto = sec.header
        _clear(recto)
        _add_italic_gray_line(recto, short_title, WD_ALIGN_PARAGRAPH.RIGHT)
        # Verso / even
        verso = sec.even_page_header
        _clear(verso)
        _add_italic_gray_line(verso, author_cite, WD_ALIGN_PARAGRAPH.LEFT)


def _add_page_field(run):
    """Insert a { PAGE } field into a run."""
    fld_char_begin = OxmlElement("w:fldChar")
    fld_char_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.text = "PAGE"
    fld_char_end = OxmlElement("w:fldChar")
    fld_char_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char_begin)
    run._r.append(instr)
    run._r.append(fld_char_end)


def _build_footer(container, copyright_line: str, *, page_on_right: bool):
    """Tab-separated footer: license on one side, page number on the other.

    Verso (even pages): page number flush left, copyright flush right.
    Recto (odd pages): copyright flush left, page number flush right.
    A 1pt top rule visually separates the footer from body text.
    """
    _clear(container)
    p = container.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    # Top rule separator
    apply_top_rule(p, hex_color="EEEEEE", width_pt=1)
    # Tab stops at right edge of text (6.5")
    p.paragraph_format.tab_stops.add_tab_stop(Pt(468), WD_ALIGN_PARAGRAPH.RIGHT)
    if page_on_right:
        # Recto (odd): copyright left, page number right
        r1 = p.add_run(copyright_line)
        r1.font.name = "Georgia"
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
        p.add_run("\t")
        r2 = p.add_run()
        r2.font.name = "Georgia"
        r2.font.size = Pt(9.5)
        r2.font.bold = True
        r2.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
        _add_page_field(r2)
    else:
        # Verso (even): page number left, copyright right
        r2 = p.add_run()
        r2.font.name = "Georgia"
        r2.font.size = Pt(9.5)
        r2.font.bold = True
        r2.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
        _add_page_field(r2)
        p.add_run("\t")
        r1 = p.add_run(copyright_line)
        r1.font.name = "Georgia"
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = RGBColor(0x88, 0x88, 0x88)


def set_running_footer(doc, copyright_line: str, section=None) -> None:
    """Static footer: license line + page number. Same content on verso and recto.

    If *section* is provided, operate only on that section object.
    When None (default), operate on all sections (backward-compatible).
    """
    if section is not None:
        section.footer.is_linked_to_previous = False
        section.even_page_footer.is_linked_to_previous = False
    sections = [section] if section is not None else doc.sections
    for sec in sections:
        _build_footer(sec.footer, copyright_line, page_on_right=True)
        _build_footer(sec.even_page_footer, copyright_line, page_on_right=False)
