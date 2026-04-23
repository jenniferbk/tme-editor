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
