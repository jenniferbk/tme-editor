"""Build the whole template into tmp_path and check its structure."""
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import build_template  # noqa: E402
from schema_order import document_violations  # noqa: E402


def _footer_types(section):
    return sorted(el.get(qn("w:type")) for el in section._sectPr.findall(qn("w:footerReference")))


def test_build_has_six_sections_both_cover_footers_and_schema_order(tmp_path):
    out = build_template.build(tmp_path / "template.docx")
    doc = Document(str(out))

    # [0] issue cover + title page, [1] editorial masthead, [2] editorial body,
    # [3] article masthead (zero margins), [4] article cover body, [5] body pages
    assert len(doc.sections) == 6
    assert _footer_types(doc.sections[3]) == ["default", "even"]   # was ["default"] only
    assert doc.sections[5].header.is_linked_to_previous is False
    assert doc.sections[5].even_page_header.is_linked_to_previous is False
    assert document_violations(doc) == [], document_violations(doc)[:5]


def test_cover_body_section_even_page_footer_is_unlinked_and_has_no_how_to_cite(tmp_path):
    out = build_template.build(tmp_path / "template.docx")
    doc = Document(str(out))
    even = doc.sections[4].even_page_footer
    assert even.is_linked_to_previous is False
    assert "HOW TO CITE" not in even._element.xml
