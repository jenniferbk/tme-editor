"""Assert the post-Moore-proof style updates land correctly."""
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from tme_template.styles import (
    register_body_style,
    register_title_style,
    register_heading_styles,
    register_remaining_styles,
)


def test_title_has_24pt_space_before():
    doc = Document()
    register_title_style(doc)
    style = doc.styles["TME Title"]
    assert style.paragraph_format.space_before == Pt(24)


def test_h3_is_bold_not_italic():
    doc = Document()
    register_heading_styles(doc)
    h3 = doc.styles["TME H3"]
    assert h3.font.bold is True
    assert h3.font.italic is False


def test_h1_and_h2_italicization_unchanged():
    doc = Document()
    register_heading_styles(doc)
    h1 = doc.styles["TME H1"]
    h2 = doc.styles["TME H2"]
    assert h1.font.bold is True and h1.font.italic is not True
    assert h2.font.bold is True and h2.font.italic is True


def test_figure_caption_is_centered_and_sticky():
    doc = Document()
    register_remaining_styles(doc)
    fc = doc.styles["TME Figure Caption"]
    assert fc.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.CENTER
    assert fc.paragraph_format.keep_with_next is True


def test_table_caption_is_centered_and_sticky():
    doc = Document()
    register_remaining_styles(doc)
    tc = doc.styles["TME Table Caption"]
    assert tc.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.CENTER
    assert tc.paragraph_format.keep_with_next is True


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
