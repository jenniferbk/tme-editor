"""LLM-based metadata extraction from a submitted manuscript .docx."""
import json
import os
import zipfile
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

import google.genai as genai
from lxml import etree
from pydantic import BaseModel


@dataclass
class AuthorMeta:
    name: str = ""
    affiliation_num: int = 1
    role: Optional[str] = None
    bio: str = ""
    email: Optional[str] = None
    corresponding: bool = False


@dataclass
class ArticleMeta:
    title: str = ""
    article_type: str = "RESEARCH ARTICLE"
    authors: List[AuthorMeta] = field(default_factory=list)
    affiliations: List[str] = field(default_factory=list)
    abstract: str = ""
    keywords: List[str] = field(default_factory=list)
    received: str = ""
    revised: str = ""
    accepted: str = ""
    published: str = ""
    doi: str = ""
    volume: int = 34
    number: int = 1
    year: int = field(default_factory=lambda: date.today().year)
    pages: str = "1–24"


def extract_manuscript_text(docx_path: str, max_chars: int | None = None) -> str:
    """Plain text of a .docx, preserving paragraph breaks. The whole document
    by default: author bios and dates often sit after the references, and
    Gemini 2.5 Flash's context holds any manuscript comfortably."""
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    with zipfile.ZipFile(docx_path) as z:
        doc_xml = z.read('word/document.xml')
    root = etree.fromstring(doc_xml)
    paragraphs = []
    total = 0
    for p in root.findall('.//w:p', ns):
        texts = [t.text or '' for t in p.findall('.//w:t', ns)]
        line = ''.join(texts).strip()
        if not line:
            continue
        paragraphs.append(line)
        total += len(line) + 1
        if max_chars is not None and total >= max_chars:
            break
    return '\n'.join(paragraphs)


EXTRACTION_PROMPT = """You are extracting submission metadata from a manuscript submitted to
The Mathematics Educator, a peer-reviewed journal.

Return ONLY a single JSON object (no prose, no code fences) with this shape:

{
  "title": "full article title",
  "authors": [
    {
      "name": "First M. Last",
      "affiliation_num": 1,
      "bio": "author bio paragraph verbatim if present in manuscript, else empty string",
      "email": "email if given, else empty string",
      "corresponding": true for the corresponding author (usually marked with a dagger or footnote)
    }
  ],
  "affiliations": [
    "Department of X, University of Y"
  ],
  "abstract": "abstract text verbatim",
  "keywords": ["keyword1", "keyword2"],
  "received": "Mon D, YYYY or empty string",
  "revised": "Mon D, YYYY or empty string",
  "accepted": "Mon D, YYYY or empty string",
  "published": "Mon YYYY or empty string",
  "doi": "doi.org/... if given else empty string"
}

Rules:
- If a bio is missing from the manuscript, return an empty string for bio; do not invent.
- affiliation_num refers to the index in the affiliations array (1-based).
- Keep the abstract verbatim. Do not paraphrase.
- If dates aren't present, leave them as empty strings.

Here is the manuscript text:
"""


class AuthorSchema(BaseModel):
    name: str
    affiliation_num: int
    bio: str
    email: str
    corresponding: bool


class MetadataSchema(BaseModel):
    """Shape the SDK enforces on Gemini's reply (response_schema)."""
    title: str
    authors: list[AuthorSchema]
    affiliations: list[str]
    abstract: str
    keywords: list[str]
    received: str
    revised: str
    accepted: str
    published: str
    doi: str


def _s(v) -> str:
    return v if isinstance(v, str) else ""


def _list_of_str(v) -> list:
    return [x for x in v if isinstance(x, str)] if isinstance(v, list) else []


def to_article_meta(data: dict) -> ArticleMeta:
    """Lenient conversion: the schema asks for strings and ints, but a model
    reply can still carry nulls or odd values, and an explicit null bypasses
    dict.get defaults. Nothing here raises on bad shape."""
    affiliations = _list_of_str(data.get("affiliations"))
    max_aff = max(1, len(affiliations))
    authors = []
    for a in data.get("authors") or []:
        if not isinstance(a, dict):
            continue
        try:
            aff = int(a.get("affiliation_num") or 1)
        except (TypeError, ValueError):
            aff = 1
        authors.append(AuthorMeta(
            name=_s(a.get("name")).strip(),
            affiliation_num=min(max(aff, 1), max_aff),
            bio=_s(a.get("bio")),
            email=_s(a.get("email")).strip() or None,
            corresponding=bool(a.get("corresponding")),
        ))
    return ArticleMeta(
        title=_s(data.get("title")).strip(),
        authors=authors,
        affiliations=affiliations,
        abstract=_s(data.get("abstract")),
        keywords=_list_of_str(data.get("keywords")),
        received=_s(data.get("received")),
        revised=_s(data.get("revised")),
        accepted=_s(data.get("accepted")),
        published=_s(data.get("published")),
        doi=_s(data.get("doi")),
    )


def extract_metadata(manuscript_text: str, api_key: Optional[str] = None) -> ArticleMeta:
    """Call Gemini Flash to extract structured metadata. Raises on API / JSON
    errors (caller surfaces them)."""
    key = api_key or os.environ.get('GEMINI_API_KEY')
    if not key:
        raise RuntimeError('GEMINI_API_KEY not set')
    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=EXTRACTION_PROMPT + manuscript_text,
        config={'response_mime_type': 'application/json', 'response_schema': MetadataSchema},
    )
    return to_article_meta(json.loads(resp.text))
