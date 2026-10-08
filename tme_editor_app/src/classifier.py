"""Gemini-powered paragraph classifier.

One batch call classifies every candidate body paragraph. Used as the primary
classifier by apply_styles; apply_styles falls back to a simpler heuristic if
the API call fails, so the app never hard-breaks on a Gemini outage.
"""
from __future__ import annotations

import json
import os
from typing import List, Optional


# Labels the classifier may emit. Everything else → treated as 'body'.
VALID_LABELS = {
    "heading_1", "heading_2", "heading_3",
    "body",
    "caption_figure", "caption_table",
    "reference",
    "block_quote",
    "list_item",
    "skip",
}

from pydantic import BaseModel


class _ClassificationItem(BaseModel):
    i: int
    label: str


class _ClassificationResponse(BaseModel):
    """Shape enforced by the SDK via response_schema."""
    classifications: list[_ClassificationItem]


_SYSTEM = """You are classifying paragraphs from a mathematics-education research article being prepared for publication in The Mathematics Educator (TME). Your job is to assign each paragraph a structural role so the layout engine can apply the right style.

Allowed labels (use exactly these strings):
- heading_1: top-level section heading. Examples: "Introduction", "Methods", "Results", "Discussion", "Conclusion", "Acknowledgements", "References", "Limitations of the Study", "Calculus, Accumulation, and Rate of Change".
- heading_2: sub-section heading inside a top-level section. Examples: "Participants", "Data Analysis Procedure", "The AR approach".
- heading_3: sub-sub-section heading.
- body: a normal body paragraph. This includes bolded labeled paragraphs like "Funding: ...", "Conflict of interest: ...", test-item instructions, fill-in-the-blanks, questions. If in doubt between a heading and body, prefer body.
- caption_figure: caption for a figure. Usually starts with "Figure" followed by a number and a period (or a blank if the number is a field code).
- caption_table: caption for a table. Usually starts with "Table" followed by a number.
- reference: a bibliography entry. Usually begins "LastName, F. (Year). Title…" with hanging indent.
- block_quote: a long indented quotation from another source.
- list_item: a numbered or bulleted list item that is part of an enumerated list.
- skip: empty, placeholder text, or non-content artifacts.

Return ONLY a JSON object of the form:
{"classifications": [{"i": 1, "label": "heading_1"}, {"i": 2, "label": "body"}, ...]}

You MUST return exactly one entry for every paragraph you were given, using the paragraph's index number (1-based, matching the input).
"""


def classify_paragraphs_with_report(
    paragraph_texts: List[str],
    *,
    title: str = "",
    abstract: str = "",
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> tuple[List[str], dict]:
    """Classify each paragraph. Returns (labels, gap report); labels are the same length/order as
    input. Raises on API / parse error — caller should fall back to heuristic.
    """
    import google.genai as genai

    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")

    # Number paragraphs 1-based; truncate very long ones so the input fits
    # comfortably even for huge articles
    def _clip(t: str, n: int = 400) -> str:
        t = t.replace("\n", " ").strip()
        return t if len(t) <= n else t[:n] + "…"

    numbered = "\n".join(
        f"[{i}] {_clip(t)}" for i, t in enumerate(paragraph_texts, 1)
    )

    context_lines = []
    if title:
        context_lines.append(f"Article title: {title}")
    if abstract:
        context_lines.append(f"Abstract (first 500 chars): {abstract[:500]}")
    context = "\n".join(context_lines)

    prompt = (
        _SYSTEM + "\n\n"
        + (context + "\n\n" if context else "")
        + "Paragraphs to classify:\n" + numbered
    )

    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": _ClassificationResponse,
            "temperature": 0,
            # Disable "thinking" — classification is a pattern-match task,
            # not a reasoning task. Cuts latency by ~3-5×.
            "thinking_config": {"thinking_budget": 0},
        },
    )
    return parse_classifications(resp.text, len(paragraph_texts))


def classify_paragraphs(paragraph_texts, **kwargs) -> List[str]:
    """Labels only; see classify_paragraphs_with_report for the gap report."""
    return classify_paragraphs_with_report(paragraph_texts, **kwargs)[0]


def parse_classifications(raw_json: str, n: int) -> tuple[List[str], dict]:
    """Turn the model's JSON into one label per paragraph plus a report of
    what had to be patched: `missing` indices default to body, `invalid`
    items (bad index or unknown label) default to body, `duplicates` are
    counted and the last one wins."""
    data = json.loads(raw_json)
    items = data.get("classifications", []) if isinstance(data, dict) else []
    by_idx: dict[int, str] = {}
    invalid = duplicates = 0
    for item in items:
        try:
            i = int(item["i"])
            label = str(item.get("label", ""))
        except (TypeError, ValueError, KeyError):
            invalid += 1
            continue
        if label not in VALID_LABELS:
            invalid += 1
            label = "body"
        if i in by_idx:
            duplicates += 1
        by_idx[i] = label
    labels = [by_idx.get(i, "body") for i in range(1, n + 1)]
    missing = sum(1 for i in range(1, n + 1) if i not in by_idx)
    return labels, {"missing": missing, "invalid": invalid, "duplicates": duplicates}
