"""The cover-page footer: HOW TO CITE (left) + license+copyright (right)."""
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

from tme_template.colors import FOOTER_CREAM, TEXT_MUTED, UGA_RED
from tme_template.oxml_helpers import (
    force_table_full_width,
    remove_cell_borders,
    set_cell_margins,
    set_cell_shading,
)


def add_cover_footer(section, *, citation: str, license_text: str,
                     copyright_text: str) -> None:
    """Place the cover footer (HOW TO CITE + CC BY 4.0) inside the given section's
    footer slot. Appears at the bottom of every page in this section.
    Since the cover section is exactly one page (with continuous break above and
    a next-page break after), it will only appear on the cover page."""
    footer = section.footer
    footer.is_linked_to_previous = False
    # Clear any existing paragraphs in the footer
    for p in list(footer.paragraphs):
        p._p.getparent().remove(p._p)

    table = footer.add_table(rows=1, cols=2, width=Inches(7.5))
    table.autofit = False
    table.columns[0].width = Inches(5.25)
    table.columns[1].width = Inches(2.25)
    force_table_full_width(table, total_width_inches=7.5, left_indent_inches=0.5)

    left, right = table.cell(0, 0), table.cell(0, 1)
    for c in (left, right):
        remove_cell_borders(c)
        set_cell_shading(c, FOOTER_CREAM)
    set_cell_margins(left, top=120, bottom=120, left=120, right=120)
    set_cell_margins(right, top=120, bottom=120, left=120, right=120)

    # Left cell: HOW TO CITE label + citation, all one paragraph
    p = left.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.2
    r_label = p.add_run("HOW TO CITE  ")
    r_label.font.name = "Arial"
    r_label.font.size = Pt(8)
    r_label.font.bold = True
    r_label.font.color.rgb = RGBColor(0xBA, 0x0C, 0x2F)
    r_cite = p.add_run(citation)
    r_cite.font.name = "Arial"
    r_cite.font.size = Pt(8)
    r_cite.font.color.rgb = RGBColor.from_string(TEXT_MUTED)

    # Right cell: license + copyright, all one paragraph, right-aligned
    p_r = right.paragraphs[0]
    p_r.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_r.paragraph_format.space_before = Pt(0)
    p_r.paragraph_format.space_after = Pt(0)
    p_r.paragraph_format.line_spacing = 1.2
    r_lic = p_r.add_run(f"{license_text}  ·  {copyright_text}")
    r_lic.font.name = "Arial"
    r_lic.font.size = Pt(8)
    r_lic.font.color.rgb = RGBColor.from_string(TEXT_MUTED)
