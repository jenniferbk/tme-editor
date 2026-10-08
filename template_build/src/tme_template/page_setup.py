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
