"""Carry ArticleMeta inside the starter .docx so Phase 2 can recover it after
the editor's browser session has expired (they leave for Word for hours).

The JSON lives in a Word document variable (w:docVars/w:docVar in settings.xml).
Word preserves document variables when it saves, a value may be up to 65,280
characters, and unlike the core-properties Comments field there is no
255-character cap."""
import json
from dataclasses import asdict, fields

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from extractor import ArticleMeta, AuthorMeta

DOCVAR_NAME = "TME_META_JSON"

# Elements that follow w:docVars in the CT_Settings schema sequence.
_DOCVARS_SUCCESSORS = (
    "w:rsids", "m:mathPr", "w:attachedSchema", "w:themeFontLang", "w:clrSchemeMapping",
    "w:doNotIncludeSubdocsInStats", "w:doNotAutoCompressPictures", "w:forceUpgrade",
    "w:captions", "w:readModeInkLockDown", "w:smartTagType", "sl:schemaLibrary",
    "w:shapeDefaults", "w:doNotEmbedSmartTags", "w:decimalSymbol", "w:listSeparator",
)


def meta_to_json(meta: ArticleMeta) -> str:
    return json.dumps(asdict(meta), ensure_ascii=False)


def _only_known(cls, d: dict) -> dict:
    names = {f.name for f in fields(cls)}
    return {k: v for k, v in d.items() if k in names}


def meta_from_json(s: str) -> ArticleMeta:
    d = _only_known(ArticleMeta, json.loads(s))
    d["authors"] = [AuthorMeta(**_only_known(AuthorMeta, a)) for a in d.get("authors", [])]
    return ArticleMeta(**d)


def _find_docvar(settings):
    docvars = settings.find(qn("w:docVars"))
    if docvars is None:
        return None, None
    for var in docvars.findall(qn("w:docVar")):
        if var.get(qn("w:name")) == DOCVAR_NAME:
            return docvars, var
    return docvars, None


def embed_meta(docx_path, meta: ArticleMeta) -> None:
    doc = Document(str(docx_path))
    settings = doc.settings.element
    docvars, var = _find_docvar(settings)
    if docvars is None:
        docvars = OxmlElement("w:docVars")
        settings.insert_element_before(docvars, *_DOCVARS_SUCCESSORS)
    if var is None:
        var = OxmlElement("w:docVar")
        var.set(qn("w:name"), DOCVAR_NAME)
        docvars.append(var)
    var.set(qn("w:val"), meta_to_json(meta))
    doc.save(str(docx_path))


def read_meta(docx_path):
    """Return the embedded ArticleMeta, or None when absent or unreadable."""
    _, var = _find_docvar(Document(str(docx_path)).settings.element)
    if var is None:
        return None
    try:
        return meta_from_json(var.get(qn("w:val")) or "")
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None
