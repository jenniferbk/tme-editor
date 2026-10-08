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

    # Tagline paragraph: ornament, italic tagline, ornament
    p1 = cell.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.space_before = Pt(4)
    p1.paragraph_format.space_after = Pt(2)
    add_red_run(p1, ORNAMENT + " ", size_pt=9.5)
    _gray_run(p1, TAGLINE, size_pt=9.5, italic=True)
    add_red_run(p1, " " + ORNAMENT, size_pt=9.5)

    # Meta line
    p2 = cell.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(4)
    _gray_run(p2, META_LINE, name="Arial", size_pt=8.5)
