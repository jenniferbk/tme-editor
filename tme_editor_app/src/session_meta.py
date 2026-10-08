"""Carry ArticleMeta inside the starter .docx so Phase 2 can recover it after
the editor's browser session has expired (they leave for Word for hours).

The JSON lives in the core-properties Comments field (dc:description), which
Word preserves on save and which needs no custom XML part."""
import json
from dataclasses import asdict, fields

from docx import Document

from extractor import ArticleMeta, AuthorMeta

MARKER = "TME-META-JSON:"


def meta_to_json(meta: ArticleMeta) -> str:
    return json.dumps(asdict(meta), ensure_ascii=False)


def _only_known(cls, d: dict) -> dict:
    names = {f.name for f in fields(cls)}
    return {k: v for k, v in d.items() if k in names}


def meta_from_json(s: str) -> ArticleMeta:
    d = _only_known(ArticleMeta, json.loads(s))
    d["authors"] = [AuthorMeta(**_only_known(AuthorMeta, a)) for a in d.get("authors", [])]
    return ArticleMeta(**d)


def embed_meta(docx_path, meta: ArticleMeta) -> None:
    doc = Document(str(docx_path))
    # python-docx's `comments` setter rejects values over 255 characters, and
    # real abstracts and bios are far longer. The XML itself has no such limit,
    # so write the dc:description element directly.
    doc.core_properties._element._get_or_add("description").text = MARKER + meta_to_json(meta)
    doc.save(str(docx_path))


def read_meta(docx_path):
    comments = Document(str(docx_path)).core_properties.comments or ""
    if not comments.startswith(MARKER):
        return None
    return meta_from_json(comments[len(MARKER):])
