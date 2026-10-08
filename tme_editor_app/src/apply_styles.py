"""Parameterized version of the legacy Moore article styling script.

Applies TME paragraph styles to a populated article starter. Detects the body
section by looking for the paragraph containing the Section 1→2 page break
(our cover-builder's structure), removes duplicated cover content pasted in
from the editor's manuscript (title, abstract, author info), and classifies
the remaining paragraphs into TME Body / TME H1 / TME Figure Caption / etc.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import List, Optional

from docx import Document
from docx.oxml.ns import qn

from article_starter import author_cite_text


# A caption label at the start of a paragraph: "Figure 1." / "Table 2:" /
# "Figure A1.". The period or colon after the number is what separates a
# caption from a body sentence like "Figure 1 depicts..." or "Tables were...".
FIG_PAT = re.compile(r"^\s*Figure\s+[A-Z]?\d+[a-z]?\s*[.:]", re.I)
TAB_PAT = re.compile(r"^\s*Table\s+[A-Z]?\d+[a-z]?\s*[.:]", re.I)
# Matches "LastName, F." or "LastName, F. M." or "LastName, F., &" — reference entry openers
REF_PAT = re.compile(
    r"^[A-ZÀ-ÖØ-Ý][\w'’\-]+,\s+[A-Z]\."
)


def _first_nonempty_run(p):
    for r in p.runs:
        if r.text and r.text.strip():
            return r
    return None


# The starter embeds exactly two section breaks before the body: masthead →
# cover (continuous) and cover → body (next page). Anything the editor pastes
# after that (a landscape section for a wide table) adds more, so count from
# the front rather than taking the last one.
STARTER_COVER_SECTION_BREAKS = 2


def _has_embedded_sectpr(p) -> bool:
    pPr = p._p.find(qn("w:pPr"))
    return pPr is not None and pPr.find(qn("w:sectPr")) is not None


def find_body_start_index(paragraphs) -> Optional[int]:
    """Index of the first body paragraph, or None when the document has no
    paragraph-embedded section break at all (a plain document: everything
    is body)."""
    breaks = [i for i, p in enumerate(paragraphs) if _has_embedded_sectpr(p)]
    if not breaks:
        return None
    k = min(STARTER_COVER_SECTION_BREAKS, len(breaks)) - 1
    return breaks[k] + 1


# "Received: March 3, 2026", "Accepted 12 May 2026", "Published online June 2026",
# "Received: 2026-03-03", "Revised 3/3/2026". The keyword alone is not enough:
# "Published in 2019, Smith found..." is a body sentence.
_MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
_DATE_LINE = re.compile(
    rf"^(?:received|revised|accepted|published)\b(?:\s+online)?\s*[:\-–—]?\s*"
    rf"(?:(?:\d{{1,2}}\s+)?{_MONTH}\s+\d{{1,2}},?\s*\d{{0,4}}"
    rf"|{_MONTH}\s+\d{{4}}"
    rf"|\d{{4}}-\d{{2}}-\d{{2}}"
    rf"|\d{{1,2}}/\d{{1,2}}/\d{{2,4}})",
    re.I,
)


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _looks_like_cover_duplicate(text: str, meta) -> bool:
    """True if a paragraph at the top of the pasted body duplicates cover
    content the starter already renders. Matches are near-equalities or
    whole-string containment, never prefixes: a heading that happens to be a
    phrase of the title, or a sentence that opens with 'Published', is body."""
    t = text.strip()
    if not t:
        return False
    tl = t.lower()
    title = (meta.title or "").strip()
    if title and (_similar(t, title) >= 0.85 or (title.lower() in tl and len(t) <= len(title) + 40)):
        return True
    abstract = (meta.abstract or "").strip()
    if abstract and len(t) >= 40 and _similar(t[:160], abstract[:160]) >= 0.85:
        return True
    if tl in {"abstract", "abstract:", "keywords", "keywords:"} or tl.startswith(("keywords:", "keywords ")):
        return True
    for a in meta.authors or []:
        if a.name and a.name.strip().lower() in tl and len(t) < 200:
            return True
    if _DATE_LINE.match(t):
        return True
    for aff in meta.affiliations or []:
        if aff and aff.strip().lower() in tl and len(t) < 200:
            return True
    if "corresponding author" in tl and len(t) < 200:
        return True
    return False


# Source paragraph styles that already say "I am a caption": Word's built-in
# "Caption", APA-template variants like "Figure Caption" / "Table Caption",
# and label styles like "FigureLabel".
_CAPTION_SRC_PAT = re.compile(r"caption|(figure|table)\s*label", re.I)


def is_caption_source_style(src_style: str) -> bool:
    return _CAPTION_SRC_PAT.search(src_style or "") is not None


def caption_style_for(src_style: str, text: str) -> str:
    """Figure vs table caption: the source style name decides when it names
    one ("Table Caption"); otherwise the text's leading word; default figure."""
    s = (src_style or "").lower()
    if "table" in s:
        return "TME Table Caption"
    if "figure" in s:
        return "TME Figure Caption"
    return "TME Table Caption" if TAB_PAT.match(text) else "TME Figure Caption"


def _assign(p, doc, style_name: str, stats: dict) -> None:
    p.style = doc.styles[style_name]
    stats["applied"][style_name] = stats["applied"].get(style_name, 0) + 1


# Mapping from Gemini classifier label → TME style name
_LABEL_TO_STYLE = {
    "heading_1": "TME H1",
    "heading_2": "TME H2",
    "heading_3": "TME H3",
    "body": "TME Body",
    "caption_figure": "TME Figure Caption",
    "caption_table": "TME Table Caption",
    "reference": "TME Reference",
    "block_quote": "TME Block Quote",
    "list_item": "List Paragraph",
    # "skip" left intentionally absent — don't restyle
}


def _heuristic_classify(t: str, p) -> str:
    """Fallback classifier when Gemini is unavailable. Same logic as the
    previous heuristic version — conservative toward 'body' on ambiguity."""
    if REF_PAT.match(t):
        return "reference"
    if FIG_PAT.match(t) and len(t) < 400:
        return "caption_figure"
    if TAB_PAT.match(t) and len(t) < 400:
        return "caption_table"
    first = _first_nonempty_run(p)
    is_bold = bool(first and first.bold)
    is_short = len(t) < 150
    is_labeled_body = ": " in t and len(t.split(": ", 1)[1].strip()) > 20
    has_fill_in = re.search(r"[_—–]{3,}", t) is not None
    tr = t.rstrip()
    ends_sentence = tr.endswith(("?", "!", ":", ",", ";"))
    ends_with_period = tr.endswith(".")
    if (is_bold and is_short
            and not is_labeled_body
            and not has_fill_in
            and not ends_sentence
            and not (ends_with_period and len(t) > 40)):
        return "heading_1"
    return "body"


def apply_styles(docx_path: str, meta) -> dict:
    """Open docx at docx_path, apply TME styles, save in place. Returns stats.

    `meta` is the ArticleMeta that was used to build this starter. Used to
    identify and remove pasted-in duplicates of the cover content, and to
    give the Gemini classifier article context.
    """
    doc = Document(docx_path)
    paragraphs = list(doc.paragraphs)

    body_start = find_body_start_index(paragraphs)
    if body_start is None:
        # Fallback: start from the paragraph after the last TME Title paragraph.
        last_title_idx = None
        for i, p in enumerate(paragraphs):
            if p.style and p.style.name == "TME Title":
                last_title_idx = i
        # No TME Title: a plain document, classify everything from paragraph 0.
        body_start = 0 if last_title_idx is None else last_title_idx + 1

    # Remove leading duplicates of cover content and any leftover placeholder
    deleted_preamble = 0
    deleted_previews = []
    placeholder_token = "paste article body here"
    while body_start < len(paragraphs):
        p = paragraphs[body_start]
        t = p.text.strip()
        tl = t.lower()
        is_placeholder = placeholder_token in tl
        if not t or is_placeholder or _looks_like_cover_duplicate(t, meta):
            if t and not is_placeholder:
                deleted_previews.append(t[:80])
            p._element.getparent().remove(p._element)
            deleted_preamble += 1
            # Refresh paragraphs list since we mutated
            paragraphs = list(doc.paragraphs)
            # body_start index refers to the next element naturally now
            continue
        break

    stats = {
        "deleted_preamble": deleted_preamble,
        "deleted_preamble_previews": deleted_previews,
        "classifier_report": {},
        "skipped_empty": 0,
        "classifier": "heuristic",  # overwritten to 'gemini' if that path runs
        "applied": {},  # style name → count
    }

    # First pass: handle paragraphs whose SOURCE style already tells us what
    # they are. This short-circuits before calling Gemini and is cheap insurance
    # against Gemini misclassifying things the source already marked.
    body_paragraphs = paragraphs[body_start:]
    pending = []  # (index_in_body_paragraphs, paragraph) for Gemini

    for i, p in enumerate(body_paragraphs):
        t = p.text.strip()
        if not t:
            stats["skipped_empty"] += 1
            continue
        src_style = p.style.name if p.style else ""

        if src_style in ("TMEReference", "TME Reference",
                         "EndNoteBibliography", "EndNote Bibliography"):
            _assign(p, doc, "TME Reference", stats)
            p.paragraph_format.left_indent = None
            p.paragraph_format.first_line_indent = None
            continue
        if src_style in ("Heading 1", "heading 1"):
            _assign(p, doc, "TME H1", stats); continue
        if src_style in ("Heading 2", "heading 2"):
            _assign(p, doc, "TME H2", stats); continue
        if src_style in ("Heading 3", "heading 3"):
            _assign(p, doc, "TME H3", stats); continue
        if src_style.startswith("TME ") and src_style != "TME Body":
            # The editor set this in Word (or a previous Finalize did); final.
            stats["applied"][src_style] = stats["applied"].get(src_style, 0) + 1
            continue
        if is_caption_source_style(src_style):
            _assign(p, doc, caption_style_for(src_style, t), stats)
            continue
        if src_style == "EndNoteBibliographyTitle":
            _assign(p, doc, "TME H1", stats)
            continue
        if src_style in ("List Paragraph", "ListParagraph"):
            # Leave as List Paragraph; style is already registered.
            continue
        if src_style in ("Normal", "", "Default Paragraph Font", "Body Text"):
            pending.append((i, p))
            continue
        # Unknown source style — let Gemini look at it too
        pending.append((i, p))

    # Second pass: ask Gemini to classify everything that's left
    pending_texts = [p.text.strip() for _, p in pending]
    labels = None
    if pending_texts:
        try:
            from classifier import classify_paragraphs_with_report
            labels, report = classify_paragraphs_with_report(
                pending_texts, title=meta.title or "", abstract=meta.abstract or "")
            stats["classifier"] = "gemini"
            stats["classifier_report"] = report
        except Exception as e:
            stats["classifier"] = f"heuristic (gemini error: {e})"
            labels = None

    # Apply classifications (Gemini if we have them, heuristic otherwise)
    for idx, (_, p) in enumerate(pending):
        t = p.text.strip()
        if labels is not None:
            label = labels[idx]
        else:
            label = _heuristic_classify(t, p)
        style_name = _LABEL_TO_STYLE.get(label)
        if style_name is None:  # "skip" or unrecognized
            continue
        _assign(p, doc, style_name, stats)
        if style_name == "TME Reference":
            p.paragraph_format.left_indent = None
            p.paragraph_format.first_line_indent = None

    # Re-establish the body section's running footer + headers. Word silently
    # relinks a newly-populated section's footer to the previous section when
    # the editor pastes into it; calling our footer builders again resets this.
    try:
        from tme_template.headers_footers import set_running_footer, set_running_headers
        cite = author_cite_text(meta)
        short_title = meta.title if len(meta.title) < 60 else meta.title[:57] + "..."
        for body_section in doc.sections[STARTER_COVER_SECTION_BREAKS:]:
            set_running_headers(doc, author_cite=cite, short_title=short_title, section=body_section)
            set_running_footer(doc, section=body_section)
        stats["footer_restored"] = True
    except Exception as e:
        stats["footer_restored"] = f"failed: {e}"

    doc.save(docx_path)
    return stats
