import shutil
import subprocess
from pathlib import Path

import pytest
from docx import Document

from moore_pipeline.endnote import resolve_endnote_citations, extract_display_text


SAMPLE_ADDIN = (
    'ADDIN EN.CITE <EndNote><Cite AuthorYear="1">'
    '<Author>von Glasersfeld</Author><Year>1995</Year>'
    '<DisplayText>von Glasersfeld (1995)</DisplayText>'
    '<record><rec-number>5</rec-number></record>'
    '</Cite></EndNote>'
)


def test_extract_display_text_finds_plain_text():
    assert extract_display_text(SAMPLE_ADDIN) == "von Glasersfeld (1995)"


def test_extract_display_text_returns_none_for_non_endnote_string():
    assert extract_display_text("not an endnote field") is None


def test_extract_display_text_handles_html_entity_encoding():
    """DisplayText sometimes contains &amp; for & — extractor should decode."""
    addin = (
        'ADDIN EN.CITE <EndNote><Cite>'
        '<DisplayText>(Ball, Thames &amp; Phelps, 2008)</DisplayText>'
        '</Cite></EndNote>'
    )
    assert extract_display_text(addin) == "(Ball, Thames & Phelps, 2008)"


def test_resolve_endnote_citations_on_moore_docx_produces_valid_output(tmp_path):
    """End-to-end: run the resolver on the real Moore manuscript and
    confirm the output opens as a valid docx and contains no ADDIN fields."""
    src = Path("/Users/jenniferkleiman/Documents/TME/TME_Moore_2026.docx")
    dst = tmp_path / "moore_resolved.docx"

    resolve_endnote_citations(str(src), str(dst))
    assert dst.exists()

    # Opens without error:
    doc = Document(str(dst))
    # Concatenate all text in the document body.
    full_text = "\n".join(p.text for p in doc.paragraphs)
    # No ADDIN markers should remain (they're the unresolved field codes):
    assert "ADDIN EN.CITE" not in full_text
    # Known citations should appear as plain text:
    assert "von Glasersfeld (1995)" in full_text or "von Glasersfeld, 1995" in full_text
