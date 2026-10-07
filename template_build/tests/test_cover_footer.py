"""The HOW TO CITE cover footer: italic segments land as italic runs."""
from docx import Document

from tme_template.cover_footer import add_cover_footer


def _cite_paragraph(section):
    for table in section.footer.tables:
        for cell in table._cells:
            for p in cell.paragraphs:
                if "HOW TO CITE" in p.text:
                    return p
    raise AssertionError("no HOW TO CITE paragraph in footer")


def test_cover_footer_renders_italic_segments():
    doc = Document()
    section = doc.sections[0]
    add_cover_footer(section, citation=[
        ("Author, A. (2026). Title. ", False),
        ("The Mathematics Educator", True),
        (", ", False),
        ("34", True),
        ("(1), 1–24.", False),
    ])
    p = _cite_paragraph(section)
    runs = p.runs[1:]  # skip the "HOW TO CITE  " label
    assert [r.text for r in runs] == [
        "Author, A. (2026). Title. ", "The Mathematics Educator", ", ", "34", "(1), 1–24.",
    ]
    assert [bool(r.font.italic) for r in runs] == [False, True, False, True, False]
    assert p.runs[0].font.bold is True  # label untouched


def test_cover_footer_still_accepts_plain_string():
    doc = Document()
    section = doc.sections[0]
    add_cover_footer(section, citation="[Author, A. (YYYY). Title.]")
    p = _cite_paragraph(section)
    assert p.runs[1].text == "[Author, A. (YYYY). Title.]"
    assert not p.runs[1].font.italic
