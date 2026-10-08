# TME editor code review — 7 October 2026

Scope: `tme_editor_app/` (Streamlit app and pipeline) and `template_build/src/`
(shared `tme_template` layout package). `moore_build/` was not reviewed; it is
legacy and the app imports one function from it (see Structure).

How this was produced: a diff review of tonight's commits (findings fixed and
pushed as e50710b and 67f87c9), then two independent whole-module reviews of
the older code. Each finding below carries a confidence tag:

- **verified** — reproduced or read end to end in this session
- **reviewer-confirmed** — the reviewer reports reproducing or tracing it
- **plausible** — the code path is real; the impact depends on inputs or Word

Line numbers refer to commit 67f87c9.

## Fixed tonight

| Commit | What |
|---|---|
| fc024c1 | Pasted figure captions keep direct alignment; now stripped so the centered style wins. HOW TO CITE footer italicizes journal and volume. |
| 5fa075c | APA 7 two-line captions merged into "Figure N. Title"; image-only body paragraphs centered; caption-like source styles mapped without the LLM. |
| e50710b | Merge walks XML siblings (a table after "Table N" no longer swallows the Note below it); page/section breaks preserved; whole-title italics dropped; anchored pictures skipped; APA 7 comma before the ampersand; hyphen to en dash in pages. |
| 67f87c9 | Only "Figure N." / "Table N:" labels become captions. Body sentences like "Table 2 presents..." and "Figures 3 and 4 show..." stay body. **verified** (was app finding 1). |

## Tier 1 — affects ordinary proofs; fix next

**A4. Body start is detected from the LAST section break.** `apply_styles.py:33`
(`find_body_start_index`, also used by `fixup.py` and the header restore). The
starter has two embedded breaks; a manuscript with a landscape section for a
wide table pastes more, so the body start lands after the landscape section.
Everything before it is never classified, images there are not centered, and
running headers are rebuilt only for the last section. Fix: take the index
after the SECOND embedded break, or place a durable sentinel (bookmark) in the
starter; restore headers for every section from the body start on.
*reviewer-confirmed (logic); whether Word carries the breaks through paste was not executed.*

**A5. The cover-duplicate heuristic deletes real content silently.**
`apply_styles.py:59-79`, loop at `:182`. With the Moore title and affiliation,
"Quantitative Reasoning" (a heading that is a substring of the title),
"Published research on u-substitution has largely focused on procedures."
(starts with a date keyword) and "Department of Mathematics faculty
participated." (first 25 characters of the affiliation) all returned True.
Only a count is recorded. Fix: near-equality for the title (similarity ratio,
not substring), a date-like pattern after the date keywords, drop or tighten
the affiliation prefix test, and record previews of deleted paragraphs for
the UI. *reviewer-confirmed by execution.*

**A3. A Gemini failure at Finalize degrades silently into the heuristic.**
`apply_styles.py:241-251`, `classifier.py:100-112`, `app.py:263, :284`.
Missing key, quota, network error, or an SDK too old for `thinking_config`
all fall into `_heuristic_classify`, which only emits reference, caption,
heading_1 (bold and short) or body. The proof loses H2/H3, lists and block
quotes while the UI shows "Proof finalized." in green. Valid JSON that omits
indices is back-filled with body and not reported. `google-genai>=0.7` permits
SDK versions that predate thinking config. Fix: `st.warning` whenever
`stats["classifier"] != "gemini"`, count and report missing indices, pass a
typed `response_schema`, raise the SDK floor to a 1.x version.
*reviewer-confirmed by reading.*

**A2. Phase 2 is unreachable after a browser refresh; the first upload is sticky.**
`app.py:94, :203, :248`. Phase 2 needs `starter_bytes` and `meta` in session
state, but the editor leaves for Word for hours; when they return the session
is gone and every manual correction must be redone. Line 94 accepts a
manuscript only while `manuscript_path` is None, so a corrected re-upload is
ignored. No reset path. Fix: persist `meta` inside the starter (custom XML
part or `docProps/custom.xml`) and read it back, or offer a meta JSON
download/upload beside the starter; replace the manuscript when the uploader's
file changes; add a Reset button. *reviewer-confirmed by reading.*

**A6. Run-level stripping skips runs inside hyperlinks.** `fixup.py:351, :406, :590`.
`Paragraph.runs` returns only direct `w:r` children (python-docx 1.2.0
`r_lst`), so runs inside `w:hyperlink` (and `w:ins`) keep their font. A
reference in Times New Roman with a hyperlinked DOI ends up Georgia except
the DOI. Fix: iterate `p._p.iter(qn("w:r"))`. *verified against python-docx source.*

**A7. Table cells come out in Calibri, not Georgia.** `fixup.py:579-600`.
`normalize_table_cells` strips fonts, but Normal has no font and docDefaults
point at the theme minor font, and cell paragraphs never get a TME style
because `doc.paragraphs` excludes tables. Fix: assign cell paragraphs a TME
style (TME Body or a new TME Table Text), or set Normal's font to Georgia in
the starter. *reviewer-confirmed on a built starter.*

**T1. Headshots ignore EXIF orientation.** `headshot.py:67`. An iPhone portrait
stored landscape with Orientation=6 is processed sideways: face detection
finds nothing, the heuristic crop runs, and the output is rotated 90°. Fix:
`ImageOps.exif_transpose(Image.open(src_path))`. *reviewer-confirmed by reproduction.*

**T2. Transparent PNG headshots get a black background.** `headshot.py:67`.
`.convert("RGB")` discards alpha and keeps the underlying RGB, usually black.
Fix: convert to RGBA and paste onto a solid RGB canvas using alpha as mask.
*reviewer-confirmed for RGBA and palette PNGs.*

**T4. Header and footer distance is left at 0.5 inch while margins are 0.3.**
`page_setup.py:12-13`. Every section has `w:header="720" w:footer="720"`;
Word pushes body text clear of header/footer content, so effective top and
bottom margins are about 0.7 inch, not 0.3. Fix: set `section.header_distance`
and `section.footer_distance` to at most the margin. *reviewer-confirmed in XML.*

## Tier 2 — robustness and correctness under less common inputs

**A8. Cover tables are skipped by index (0, 1).** `fixup.py:579, :614, :646`.
Assumes Word merged masthead and tagline into one table. If they stay
separate, the author card (index 2) is centered, every row gets
cantSplit/tblHeader, and names and bios lose font and size. Fix: treat every
`w:tbl` before the body-start break as a cover table. *plausible.*

**A11. Headshot widgets can crash the page and leak temp dirs.** `app.py:63,
:158-172, :178, :244`. Selectbox key is the uploaded filename, so two files
both named `headshot.jpg` raise a duplicate-key error until refresh.
`_save_upload` runs for every matched headshot on every rerun (each
keystroke), creating a new `mkdtemp` each time; none of the four `mkdtemp`
sites is cleaned. Fix: key by index; save only inside the Build handler; one
per-session work dir removed on reset. *reviewer-confirmed by reading.*

**A12. Extracted metadata is not validated; JSON null bypasses defaults.**
`extractor.py:113-134`, `app.py:142`. `dict.get(key, default)` returns None
on an explicit null. A null author name crashes `_format_citation`; a null
title fails at `len(meta.title)`; a non-integer `affiliation_num` reaches
`st.number_input` outside any try and repeats on every rerun. Fix: pydantic
schema as `response_schema`, coalesce with `or`, clamp `affiliation_num`.
*reviewer-confirmed (null); number_input behavior plausible.*

**A13. Only the first 20,000 characters reach Gemini.** `extractor.py:41, :57`.
Roughly 3,000 words; bios or dates after the references are never seen and
come back blank with no indication. Fix: send the whole text, or head plus
tail. *verified truncation; where bios sit is manuscript-dependent.*

**A14. Any indented body paragraph becomes a gray block quote.** `fixup.py:118,
:136`. A left indent over 20pt on TME Body suffices, so indented task
sub-parts "(a) Sketch the graph..." become TME Block Quote. Fix: require an
additional signal (right indent, length, or Gemini's own label), or make it
report-only. *plausible.*

**A15. Heading source styles, including the app's own, are re-judged by Gemini.**
`apply_styles.py:231-235`. Word's Heading 1/2/3 and TME H1/H2/H3 fall through
to the LLM; an editor who fixes a heading in Word and re-finalizes can have
it undone. Fix: map Heading 1/2/3 deterministically; treat TME-prefixed
source styles as final. *path confirmed; relabel frequency plausible.*

**T3. The HOW TO CITE footer exists for odd pages only.** `cover_footer.py:29-30`
with `page_setup.py:16` turning on different odd/even. Only
`footerReference type="default"` is written; an undefined even footer is
blank. Single articles put the cover on page 1 and are fine; an assembled
issue loses the footer on every even-page cover. Fix: populate
`section.even_page_footer` too. *reviewer-confirmed for XML; Word behavior spec-based.*

**T5. Children appended to `w:pPr` and `w:tblPr` out of schema order.**
`oxml_helpers.py:52-57, :131-181`. All `w:pBdr` elements land after
`w:ind`/`w:jc`/`w:spacing`; tables through `force_table_full_width` have tblW,
tblInd, tblLayout, tblCellMar after tblLook. Word on this Mac tolerates it;
validators, Google Docs or Pages import, and some Word builds may drop the
rules or the width. Fix: `insert_element_before(...)` with the schema
successors; `table.autofit = False` already writes tblLayout natively.
*order violation confirmed; rendering impact plausible.*

**T6. Column widths written to gridCol only, leaving stale tcW values.**
`front_matter.py:69, :184-185`, `masthead.py:57-58`. Word prefers tcW,
LibreOffice gridCol, so the masthead split depends on the renderer.
`tagline.py:50-61` hand-patches tcW for this reason but misattributes the
cause: python-docx substitutes a 1-inch margin when a margin is zero, so
tables in a zero-margin section default to 6.5 inches. Fix: set `cell.width`
on every cell alongside `column.width`, then delete the manual tcW code in
tagline.py and cover_page.py:157-165. *mismatch confirmed; rendering difference plausible.*

**T7. The H1 red rule and pullquote rules are never applied.** `styles.py:41-43, :51`;
`oxml_helpers.py:73`. The 10pt indent is reserved for a rule that nothing
draws; a repo-wide grep finds zero call sites for `apply_red_left_rule` or
`apply_pullquote_rules`. The README claim that borders cannot live on a
paragraph style is wrong; `w:pBdr` is valid in a style's pPr. Fix: add the
border to the style once and delete the helpers, or drop the indent. *reviewer-confirmed.*

**T8. Heading styles have no outline level.** `styles.py:44-75`. Navigation pane,
TOC, PDF bookmarks and accessibility checks see a flat document. Fix:
`get_or_add_outlineLvl()` with 0/1/2, or base on built-in Heading 1-3.
*reviewer-confirmed absence.*

**T9. Custom styles lack qFormat, so they are hidden from the Styles gallery.**
`styles.py:9-13`. Fix: `style.quick_style = True`. *reviewer-confirmed.*

**T10. Headshot circle is aliased; no-face fallback is silent; cascade load unchecked.**
`headshot.py:17, :69-74, :78-79`. Mask drawn at output resolution (edge jumps
255 to 0); heuristic crop runs with no signal; `cascade.empty()` never
checked. Fix: draw the mask at 4x and downsample with LANCZOS; return whether
a face was found; raise clearly when the cascade is empty. *aliasing reviewer-confirmed by probe.*

**T11. Inconsistent missing-image handling.** `cover_page.py:172-174` raises
and aborts; `masthead.py:75-82` catches FileNotFoundError and prints;
`front_matter.py:93-98` catches OSError and prints. Only the portrait logo
goes through `_open_image_as_rgb_stream`. Fix: one policy (raise in library
code, decide in the app), `logging.warning` not print, both logos through the
same RGB normalizer. *reviewer-confirmed.*

**T12. Page 2 of the issue template starts only by overflow arithmetic.**
`build_template.py:46-51`, `front_matter.py:75-80, :212-213`. The issue cover
is a 9-inch at-least row and the title page opens with a 120pt spacer; they
separate only because the sum exceeds the 10.4-inch body height. Change the
row height, margins or spacer and pages 1 and 2 merge. The comment at
`front_matter.py:75` still says 1-inch margins. Fix: an explicit page break or
next-page section break after the issue cover. *confirmed by arithmetic.*

**T13. python-docx Section objects alias the newest section after a later `add_section`.**
`add_section_break` reuses the sentinel sectPr and clones it to close the old
section, so a Section obtained earlier silently points at the newest one.
`build_template.py` and `article_starter.py` are safe only because every
mutation precedes the next break. Fix: a warning comment at the top of each
builder, or re-fetch via `doc.sections[i]` before mutating. *confirmed from
source; no current bug.*

**T14. The 8.563-inch bleed is tuned to Compatibility Mode 14.** `masthead.py:50-58`,
`tagline.py:39-44`; generated `settings.xml` pins compatibilityMode 14 from
python-docx's default template. If an editor clicks Convert, or the file
renders in LibreOffice or Word for Windows in mode 15, the gap reappears or
the table overflows the page edge. The zero-margin-section plus
continuous-break design exists only for this bleed. Fix: a negative `tblInd`
on a table inside a normal-margin section gives full bleed with one section
per page, which also removes the odd/even footer dependency in T3. *compat
mode confirmed; rendering plausible.*

## Tier 3 — cleanup

- **A9.** `strip_reference_run_formatting` (`fixup.py:346`) removes the same five
  run tags as `strip_direct_formatting`, which already targets TME Reference.
  Delete it. *verified.*
- **A10.** Headshots are JPEG-compressed twice: `pipeline.py:36-40` re-encodes
  at quality 92, then `headshot.py:67` at 90; `_to_sRGB_jpg` duplicates
  `moore_pipeline/headshots.py:10`. Pass the upload straight through. The
  uploader accepts `.avif` but the `Pillow>=10.4` floor may resolve to a
  version without AVIF support on a fresh deploy [VERIFY first Pillow release with built-in AVIF].
- **Dockerfile** installs `/app/tme_editor_app/requirements.txt`, which does not
  exist (only the repo-root file does), so the image build fails. *verified.*
- **README drift:** says to pip install from `tme_editor_app/`, mentions a
  "companion styling script" instead of Phase 2, omits apply_styles,
  classifier and fixup from the layout.
- **Structure:** the app installs `moore_build` only for
  `resolve_endnote_citations` (`pipeline.py:9`). Move that one module into the
  app or `tme_template` and drop the package from requirements. *verified.*
- Running-header text is computed twice with different guards
  (`article_starter.py:125`, `apply_styles.py:274`); three or more authors
  render "A & B & C". One helper; consider "A et al.".
- `REF_PAT` and `_REF_OPENER` are duplicated (`apply_styles.py:21`,
  `fixup.py:115`) and miss lowercase particles, multi-word surnames and
  corporate authors ("van Hiele, P. M. (1986)." and "National Council of
  Teachers of Mathematics. (2014)." both fail).
- `fix_masthead_grid` hardcodes twips (`fixup.py:655`) that are one twip off
  the generated grid; derive from the masthead constants.
- `swap_captions_above` matches its target by an 80-character text prefix
  (`fixup.py:522`) and, for figures, accepts any preceding text paragraph with
  no image check (`:566`). Re-resolve by element identity.
- `fix_footnote_fonts` (`fixup.py:739`) rewrites every rFonts to Georgia,
  including Symbol and Cambria Math runs, changing glyphs.
- Caption styles get keep_with_next; for a below-element caption left in place
  this glues it to the following body paragraph, not its figure.
- `fix_content_tables` (`fixup.py:641`) marks row one of every content table
  as a repeating header, including layout tables.
- `ArticleMeta` hardcodes volume 34, number 1, year 2026, pages "1–24"; the
  extractor never asks for them and the year default goes stale.
- Smaller: `_style()` unused (`apply_styles.py:89`); `_proof_filename` and
  `_starter_filename` duplicated; review widgets without a key feed their own
  return value back as default.

Template package (`template_build/src/`):

- Dead code: `set_different_first_page` and `set_explicit_tbl_grid`
  (`oxml_helpers.py:47, :184`); `_section_label` and `_role_group` doc-level
  variants (`front_matter.py:137-154`); unused `field` import in
  `cover_page.py:2` and `front_matter.py:3`; `AuthorEntry.role` never
  rendered; the `issue` parameter of `add_editorial_staff_page` unused.
- Hand-rolled OOXML that python-docx 1.x provides natively:
  `set_different_odd_even_pages` is
  `doc.settings.odd_and_even_pages_header_footer = True`; the trHeight code in
  `front_matter.py:76-80` is `row.height` and `row.height_rule`;
  `_get_or_add_paragraph_style` can use `name in doc.styles`.
- `oxml_helpers.py:140` has a no-op conditional and a dead insert branch
  (tblPr always exists on a python-docx table).
- `_red_run` is defined three times (`front_matter.py`, `tagline.py`,
  `cover_page.py` as `_red_label`); `TOTAL_WIDTH` and `BLEED_INCHES` are
  duplicated in `masthead.py` and `tagline.py`.
- `cover_page.py:145` applies "Table Grid" and then removes every border; the
  default table style gives the same result with less XML and no dependency on
  that style existing in the host document.
- `build_template.py` re-sets page width and height on every new section
  although `add_section` clones the previous sectPr.
- The U+25C6 black diamond in `tagline.py:70-72` is in neither Georgia nor
  Arial, so Word substitutes a symbol font that differs between Mac and Windows.
- `masthead.py:100` adds an empty paragraph when doi is None, leaving a blank
  line in the red panel. `masthead.py:59` sets row height without a height rule.
- `headshot.py`: prefer `with Image.open(...)` and `Image.Resampling.LANCZOS`;
  `minSize=(60, 60)` is absolute pixels, so small source images never detect a face.

## Tests

All 40 app tests and 17 template tests pass. Well covered: split-caption
merge, image centering, caption position report and swap, alignment strip,
source-style caption mapping, caption-label rule, citation format, template
styles, running footer, headshot framing, colors.

Not covered: `apply_styles` end to end; classifier parsing (missing, duplicate
or invalid indices); extractor; `remap_block_quotes`; hyperlink runs in the
strip functions; table fixes against a real starter; `fix_footnote_fonts`;
headshot EXIF and alpha handling; OOXML element order.

Template package: no test runs `build()`, so the five-section structure,
footer references and zero-margin sections are unverified. `masthead.py`,
`tagline.py`, `front_matter.py`, `page_setup.py` and `oxml_helpers.py` have no
tests, contrary to the README. No test checks XML child order. The headshot
tests never exercise a face, EXIF orientation, alpha, or the no-face path.
`test_headers_footers_update.py:17` would pass on the literal text "PAGE".
`test_colors.py` asserts constants equal themselves. First additions: a golden
build into `tmp_path` asserting sectPr count and reference types, and a
schema-order helper that walks every pPr, tcPr and tblPr against
python-docx's own `_tag_seq` lists.

`tme_editor_app/test_pipeline.py` is dead: it defines no test functions and
its fixtures (`TME_Moore_2026.docx`, headshot JPEGs) are gitignored, so
pytest collects nothing. *verified.*

Highest-value addition: one golden test that builds a starter, injects a
synthetic pasted body (headings, body sentences starting with "Figure", APA
split captions, references with a hyperlinked DOI, a table, an indented
list), monkeypatches `classifier.classify_paragraphs` with fixed labels, runs
`apply_styles` then `run_fixup`, and asserts each paragraph's style and that
the author card is untouched.

## What is working well and should stay

The two-phase architecture (build a cover starter, let the editor paste in
Word, then classify and fix up) fits the problem. Each fixup step is a small
named function on a Document that returns stats, which is why tonight's
split-caption work could be added and tested in isolation. The deterministic
source-style short-circuit before the LLM call is cheap insurance in the
right order. The low-level XML work is careful: `qn()` everywhere, lxml
sibling operations used correctly, the footnote rewrite deliberately
sequenced after the python-docx save. The classifier call is well tuned
(temperature 0, JSON mime type, thinking disabled, clipped inputs), and
leaving "skip" unmapped is sensible.

Template package: the module split is clean and each file owns one visual
concern. Inputs are typed dataclasses, and the color palette has a single
source of truth with a test guarding it. Comments explain why rather than what
for the Word quirks (CMYK logo, List Paragraph override, the bleed). The
`section=` parameter and unlinking logic in `headers_footers.py` are correct,
and the citation-segments API in `cover_footer.py` is a small clean design. The
OpenCV pin below 5 is enforced in pyproject, requirements and a loud test.

## How the review was verified

Diff review: the three commits since the previous push, findings fixed and
re-tested in this session. Older code: two independent read-only reviewers,
one per package. The template reviewer read every file, checked python-docx
1.2.0 source in the project venv, built the template into a scratch directory
(the repo's `TME_Template_2026.docx` was not touched) and inspected the
resulting XML; the EXIF, alpha and circle-edge headshot findings were
reproduced with synthetic images. The app reviewer read every file against
commit e50710b and executed the caption-pattern and cover-duplicate
heuristics. Items marked *verified* were re-checked directly in this session.
