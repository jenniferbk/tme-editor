# TME template — post-Moore-proof changes

**Date:** 2026-04-23
**Target tree:** `tme-editor/` (deployed repo). After merge, mirror to local `~/Documents/tme/` iteration workspace.
**Origin:** Editor feedback after sending out the `TME_Moore_2026` proof. All changes are template-level — every future issue inherits them. No Moore-specific overrides.

## Goals

1. Tighten the cover's vertical rhythm (title–banner breathing room).
2. Reorder the cover so "About the Authors" sits above the abstract.
3. Simplify the body running footer to just a page number.
4. Align caption placement with APA 7 (above, flush left, single-line format).
5. Make the color palette deliberate and documented.
6. Make heading italicization consistent with APA 7.

A secondary goal is to explicitly document decisions that result in *no* change (font policy, Title alignment, H1 red rule) so a future editor knows they were considered.

## Non-goals

- No changes to fonts. Arial stays where it is.
- No changes to `TME_Moore_2026_starter.docx` beyond re-running the pipeline to pick up the new template.
- No change to Title alignment (stays flush-left).
- No change to H1's red left rule.
- No automatic rewrite of below-element figure/table captions; only opt-in.

## Architecture

Changes split across two Python packages and one generated artifact:

- **`template_build/src/tme_template/`** — the paragraph/cover/masthead styles that every article inherits.
- **`tme_editor_app/src/`** — the Streamlit-driven fixup that runs on a pasted-populated starter.
- **`TME_Template_2026.docx`** — the built template; rebuilt from source by `template_build/src/build_template.py` after the refactor.

No new modules. All changes are edits to existing files.

## Design

### 1. Cover title spacing

**File:** `template_build/src/tme_template/styles.py`

`register_title_style` currently sets `TME Title` with `space_before = Pt(0)`. Change to `space_before = Pt(12)`. Combined with the tagline strip's existing `space_after=4pt`, that gives a 16pt gap, matching the existing 8+8 rhythm around the dates row.

### 2. "About the Authors" above the abstract

**File:** `template_build/src/tme_template/cover_page.py`

Reorder the block sequence in `add_research_article_cover` from:

> title → authors → affiliations → corresponding → dates → rule → ABSTRACT → abstract text → keywords → rule → ABOUT THE AUTHORS → author-card table

to:

> title → authors → affiliations → corresponding → dates → rule → **ABOUT THE AUTHORS → author-card table** → rule → **ABSTRACT → abstract text → keywords**

The rule placements move with the blocks; we don't add a new rule. Spacing constants on each block stay the same.

### 3. Body running footer = page number only

**Files:** `template_build/src/tme_template/headers_footers.py`, `tme_editor_app/src/article_starter.py`

`set_running_footer` drops its `copyright_line` parameter. `_build_footer` emits one centered paragraph containing the `{PAGE}` field (Georgia 9.5pt bold, color `INK`). The existing 1pt top rule stays for visual separation from body text. Recto/verso symmetry is preserved (both pages get a centered page number).

`article_starter.build_article_starter` stops computing and passing `copyright_line`. The cover footer (`cover_footer.py`) is untouched — `HOW TO CITE [citation] · CC BY 4.0 · © {year} The Authors` remains on page 1.

### 4. Caption format (APA 7)

**Files:** `template_build/src/tme_template/styles.py`, `tme_editor_app/src/fixup.py`

**Styles:** both `TME Figure Caption` and `TME Table Caption` become:
- `alignment = LEFT`
- `keep_with_next = True` (on the caption itself)
- Same font/size/color as before (Georgia 10pt, `TEXT_MUTED`).

The caption text is a single paragraph rendered as `**Figure N.** *Title.*` — authors paste whatever they have; the editor hand-formats "Figure N." as bold (or Arial bold red caps per `EDITOR_GUIDE.md` step 5) and the title portion as italic.

The incorrect comment in `styles.py` that says "Figure captions go BELOW figures (APA 7)" gets deleted.

**Fixup:**

- Remove `glue_figures_to_captions` and its call in `run_fixup`. It set `keep_with_next` on the paragraph *above* the caption, which was correct when captions went below figures.
- Add `report_below_element_captions(doc) -> list[dict]` that scans paragraphs and returns a list of `{index, kind: "figure"|"table", preview: str}` for every caption paragraph that sits directly after (rather than before) its figure or table. Detection:
  - A `TME Figure Caption` paragraph where the preceding non-empty paragraph contains an image (`w:drawing` or `w:pict`).
  - A `TME Table Caption` paragraph where the preceding block is a `w:tbl`.
- Add `swap_captions_above(doc, indices) -> int` that, for each reported index, moves the caption paragraph's XML element so it appears before its figure/table. Python-docx doesn't offer a direct move for caption↔image; we operate at the XML level: detach the caption `w:p`, find the target insertion point (the figure paragraph or the `w:tbl`), and insert the caption immediately before it. Returns count moved.
- `run_fixup` calls `report_below_element_captions` and includes the list in its returned stats dict under `captions_below_element`.
- The Streamlit app's Phase 2 panel renders the list as a warning ("N figure/table captions appear below their figure/table — APA 7 puts them above"), with an opt-in checkbox "Also try to move these above" that, when checked, invokes `swap_captions_above` after the normal fixup run.

### 5. Font policy (no change)

Every existing non-Georgia use stays. Arial continues to carry the display/chrome role (masthead metadata, tagline meta line, red cover labels, dates row, cover footer, front-matter red labels, issue-cover credit, hand-styled caption number). This is documented here so the decision isn't revisited.

### 6. Deliberate 5-step grayscale palette

**File:** `template_build/src/tme_template/colors.py`, with replacements across every file that currently uses a gray hex literal.

New palette constants:

```python
INK             = "111111"  # Title, H1, H2, H3, body text
BLOCKQUOTE_INK  = "333333"  # Block Quote only — intentionally one step lighter
TEXT_MUTED      = "444444"  # captions, footnote, cover-footer text, page number, issue credit
META            = "777777"  # dates values, affiliations, tagline italic, running-footer text,
                            # front-matter role labels, dates labels
LINE            = "BBBBBB"  # cover rules, date separators, footer top rule
```

Kept as-is:

```python
UGA_RED           = "BA0C2F"   # masthead, red labels, ornaments
BLACK             = "000000"   # masthead left cell only
LIGHT_PANEL_GRAY  = "F5F5F5"   # tagline strip background
FOOTER_CREAM      = "FAFAF7"   # cover footer background
```

Removed:

- `TAGLINE_GRAY` (superseded by `META`)
- `RULE_GRAY` (unused; superseded by `LINE`)

**Migration of existing literals.** Every raw `RGBColor(0xNN, 0xNN, 0xNN)` or hex string in the template/editor-app source gets replaced with the nearest palette step. The migrations that cause a *visible* color change (beyond "snap to nearest"):

| Location | Old | New | Note |
|---|---|---|---|
| `TME H3` text color | `#333` | `INK #111` | With change 7 H3 is also getting bolder; darker reads fine. |
| Dates labels | `#888` | `META #777` | Slightly darker. |
| Running-footer © text | `#888` | n/a | Copyright line removed entirely (change 3). |
| Date separator `·` | `#999` | `LINE #BBB` | Slightly lighter dot. |
| Cover rules | `#CCC` | `LINE #BBB` | Slightly darker rule. |
| Footer top rule | `#EEE` | `LINE #BBB` | Slightly darker — acceptable for a 1pt rule. |
| Cover-footer text | `#444` | `TEXT_MUTED #444` | No change, just named. |
| Tagline italic `#555` | `#555` | `META #777` | Slightly lighter. |
| Corresponding author italic | `#555` | `META #777` | Slightly lighter. |
| Front-matter role italic | `#666` | `META #777` | Slightly lighter. |
| Issue-cover credit italic | `#777` | `META #777` | No change, just named. |
| Pullquote | `#1A1A1A` | `INK #111` | Negligible visual change. |
| H2 color | `#222` | `INK #111` | Slightly darker. |
| Wordmark / page number | `#222` | `INK #111` | Slightly darker. |
| Block Quote | `#333` | `BLOCKQUOTE_INK #333` | Same value, now named. |

None of these are meaningful design shifts — they're a consolidation. If any single one looks wrong after build, we tune *that one* in `colors.py` without re-opening the palette.

### 7. Heading italicization per APA 7

**File:** `template_build/src/tme_template/styles.py`

`register_heading_styles` currently sets:

- `TME H1`: bold, not italic → keep
- `TME H2`: bold italic → keep
- `TME H3`: not bold, italic → **change to: bold, not italic**

Also update H3's color to `INK` (per change 6). Size (11.5pt) and spacing unchanged. `keep_with_next`/`keep_together` unchanged.

Title: flush-left stays (confirmed). H1 red rule stays (confirmed).

## Downstream effects (same PR)

- **Rebuild** `TME_Template_2026.docx` by running `template_build/src/build_template.py` after source changes land.
- **Rerun** the editor pipeline end-to-end on Moore inputs (cover extraction is skipped — reuse `TME_Moore_2026_starter.pre-fixup.docx` as the paste-state input) to produce a refreshed `TME_Moore_2026_proof.pdf`. Visual QA vs. the previous proof.
- **`EDITOR_GUIDE.md`:** no update required. The hand-styling instructions (bold + italic caption structure, Arial red caps for caption number) still apply.

## Testing

Before/after offline smoke test: `tme_editor_app/test_pipeline.py` builds Phase 1 from a fixture `ArticleMeta` and runs Phase 2 fixup on the existing Moore pre-fixup backup. Assertions after this change:

- Cover block ordering: the ABOUT THE AUTHORS paragraph label precedes the ABSTRACT label (assert by paragraph index in the output docx).
- Title style has `space_before == Pt(12)`.
- H3 style has `bold == True` and `italic == False`.
- Both caption styles have `alignment == LEFT` and `keep_with_next == True`.
- Body running footer paragraph contains a PAGE field and no literal "©" or "CC BY" string.
- `run_fixup` stats dict includes `captions_below_element` as a (possibly empty) list.
- Where the test input has a caption below a figure, that caption's index appears in `captions_below_element`.
- Every color in `colors.py`'s old set is either still present (kept ones) or explicitly removed; no orphan import leaves behind.

Visual QA on a generated proof: title breathing room; author block precedes abstract; body footer shows page number only; captions flush-left above their elements; H3 looks bold not italic; no obvious color regressions.

## Rollback

All changes are in Python source. If a change in production output looks wrong, revert the specific file's edits (the PR is structured so each change is a separate commit keyed to its section number) and rebuild the template.

## Open questions (none blocking)

- Whether to continue rendering a visible figure/table caption number as Arial red caps (per `EDITOR_GUIDE.md` step 5) or fold that into the caption style itself (automated). Out of scope for this PR — noted for a future conversation.
