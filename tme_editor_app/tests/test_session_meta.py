"""ArticleMeta rides inside the starter so Phase 2 can recover it."""
from docx import Document

from extractor import ArticleMeta, AuthorMeta
from session_meta import embed_meta, meta_from_json, meta_to_json, read_meta


def _meta():
    return ArticleMeta(title="T", authors=[AuthorMeta(name="Ada Lovelace", corresponding=True)],
                       affiliations=["UGA"], abstract="a", keywords=["k"], volume=34, number=2)


def test_round_trip_through_json():
    m = meta_from_json(meta_to_json(_meta()))
    assert m == _meta()


def test_unknown_keys_from_a_newer_starter_are_ignored():
    s = meta_to_json(_meta()).replace('"title": "T"', '"title": "T", "future_field": 1')
    assert meta_from_json(s).title == "T"


def test_embed_and_read_back(tmp_path):
    path = tmp_path / "s.docx"
    Document().save(path)
    embed_meta(path, _meta())
    assert read_meta(path) == _meta()


def test_long_metadata_survives_embedding(tmp_path):
    m = _meta()
    m.abstract = "Long abstract. " * 400
    m.authors[0].bio = "Bio with accents é and dashes – " * 50
    path = tmp_path / "long.docx"
    Document().save(path)
    embed_meta(path, m)
    assert read_meta(path) == m


def test_document_without_meta_reads_none(tmp_path):
    path = tmp_path / "plain.docx"
    Document().save(path)
    assert read_meta(path) is None
