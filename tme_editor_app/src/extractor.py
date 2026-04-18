"""LLM-based metadata extraction from a submitted manuscript .docx."""
import json
import os
import zipfile
from dataclasses import dataclass, field
from typing import List, Optional

import google.genai as genai
from lxml import etree


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
    year: int = 2026
    pages: str = "1–24"


def extract_manuscript_text(docx_path: str, max_chars: int = 20000) -> str:
    """Return the plain text of a .docx up to max_chars, preserving paragraph
    breaks. Enough to give the LLM the full front matter and a chunk of body."""
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
        if total >= max_chars:
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
      "email": "email if given, else null",
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


def extract_metadata(manuscript_text: str, api_key: Optional[str] = None) -> ArticleMeta:
    """Call Gemini Flash to extract structured metadata. Returns an ArticleMeta.
    Raises on API / JSON errors (caller should surface to user)."""
    key = api_key or os.environ.get('GEMINI_API_KEY')
    if not key:
        raise RuntimeError('GEMINI_API_KEY not set')
    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=EXTRACTION_PROMPT + manuscript_text,
        config={'response_mime_type': 'application/json'},
    )
    data = json.loads(resp.text)
    authors = [
        AuthorMeta(
            name=a.get('name', ''),
            affiliation_num=a.get('affiliation_num', 1),
            bio=a.get('bio', '') or '',
            email=a.get('email') or None,
            corresponding=bool(a.get('corresponding', False)),
        )
        for a in data.get('authors', [])
    ]
    return ArticleMeta(
        title=data.get('title', ''),
        authors=authors,
        affiliations=data.get('affiliations', []),
        abstract=data.get('abstract', ''),
        keywords=data.get('keywords', []),
        received=data.get('received', '') or '',
        revised=data.get('revised', '') or '',
        accepted=data.get('accepted', '') or '',
        published=data.get('published', '') or '',
        doi=data.get('doi', '') or '',
    )
