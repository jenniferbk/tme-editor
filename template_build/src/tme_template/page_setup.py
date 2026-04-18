"""Configure page size, margins, and odd/even pages."""
from docx.shared import Inches

from tme_template.oxml_helpers import set_different_odd_even_pages


def configure_page_setup(doc) -> None:
    """US Letter, tight top/bottom margins (0.3"), 0.5" left/right, odd/even pages distinct."""
    for section in doc.sections:
        section.page_width = Inches(8.5)
        section.page_height = Inches(11)
        section.top_margin = Inches(0.3)
        section.bottom_margin = Inches(0.3)
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)
    set_different_odd_even_pages(doc)


def configure_zero_margins(section) -> None:
    """Set all four margins on a section to zero."""
    section.top_margin = Inches(0)
    section.bottom_margin = Inches(0)
    section.left_margin = Inches(0)
    section.right_margin = Inches(0)
