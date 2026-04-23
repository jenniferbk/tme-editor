"""Assert About-the-Authors comes before Abstract on the cover page."""
from docx import Document

from tme_template.cover_page import AuthorEntry, CoverData, add_research_article_cover
from tme_template.styles import (
    register_body_style, register_title_style,
    register_heading_styles, register_remaining_styles,
)


def _build_sample_cover():
    doc = Document()
    register_body_style(doc)
    register_title_style(doc)
    register_heading_styles(doc)
    register_remaining_styles(doc)
    add_research_article_cover(doc, CoverData(
        title="Sample Title",
        authors=[
            AuthorEntry(name="Ada Lovelace", affiliation_num=1, role=None,
                        bio="Mathematician.", headshot_path=None,
                        corresponding=True, email="ada@example.edu"),
            AuthorEntry(name="Grace Hopper", affiliation_num=1, role=None,
                        bio="Computer scientist.", headshot_path=None,
                        corresponding=False, email=None),
        ],
        affiliations=["Example University"],
        dates={"Received": "Jan 1", "Revised": "Feb 1",
               "Accepted": "Mar 1", "Published": "2026"},
        abstract="This is the abstract.",
        keywords=["alpha", "beta"],
    ))
    return doc


def _first_index_of(doc, text_fragment: str) -> int:
    for i, p in enumerate(doc.paragraphs):
        if text_fragment in p.text:
            return i
    raise AssertionError(f"'{text_fragment}' not found in cover")


def test_about_the_authors_precedes_abstract():
    doc = _build_sample_cover()
    about_idx = _first_index_of(doc, "ABOUT THE AUTHORS")
    abstract_idx = _first_index_of(doc, "ABSTRACT")
    assert about_idx < abstract_idx, (
        f"Expected ABOUT THE AUTHORS (idx {about_idx}) before ABSTRACT "
        f"(idx {abstract_idx})"
    )


def test_abstract_precedes_keywords():
    doc = _build_sample_cover()
    abstract_idx = _first_index_of(doc, "ABSTRACT")
    keywords_idx = _first_index_of(doc, "Keywords:")
    assert abstract_idx < keywords_idx
