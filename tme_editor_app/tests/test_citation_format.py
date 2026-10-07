"""The cover-footer citation italicizes the journal name and volume (APA 7)."""
from extractor import ArticleMeta, AuthorMeta
from article_starter import _format_citation


def _meta():
    return ArticleMeta(
        title="A Short Title",
        authors=[AuthorMeta(name="Ada B. Lovelace"), AuthorMeta(name="Carl Gauss")],
        volume=34, number=1, year=2026, pages="1–24",
    )


def test_citation_text_reads_as_one_apa_line():
    segments = _format_citation(_meta())
    text = "".join(t for t, _ in segments)
    assert text == (
        "Lovelace, A. B. & Gauss, C. (2026). A Short Title. "
        "The Mathematics Educator, 34(1), 1–24."
    )


def test_citation_italicizes_journal_name_and_volume_only():
    segments = _format_citation(_meta())
    italic = [t for t, i in segments if i]
    assert italic == ["The Mathematics Educator", "34"]
