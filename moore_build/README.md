# Moore Article Pipeline

Automated preprocessing for producing the camera-ready PDF of the Moore article (TME Vol 34 No 1 2026).

## What this does

1. Resolves the EndNote citation field codes in the author-submitted `TME_Moore_2026.docx` to plain text (otherwise Word displays them as garbled markup).
2. Converts `Moore_Kevin.avif` to JPG and frames all three headshots (Moore, Yasuda, Wong) to 300×300 pixel squares centered on each face.
3. Generates `TME_Moore_2026_cover.docx` — a standalone Word document containing the complete Moore cover page (masthead, title, authors with superscript affiliations and red corresponding-author marker, dates row, abstract, keywords, author block with framed headshots and verbatim bios, and the CC BY 4.0 cover footer).

## What this doesn't do

Style application, figure captioning, page numbering, and final PDF export are manual Word steps — see `MERGE_INSTRUCTIONS.md`. Full automation of these would add significant complexity for little gain; Jennifer can do them in ~20 minutes with her eyes on the result.

## To run

```bash
cd moore_build
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python src/build_moore_cover.py
```

Outputs:
- `moore_build/intermediate/Moore_resolved.docx`
- `moore_build/assets/{moore,yasuda,wong}_framed.jpg`
- `TME_Moore_2026_cover.docx` (in the TME root)

## To run tests

```bash
.venv/bin/pytest -v
```

## File responsibilities

| File | What it does |
| --- | --- |
| `src/moore_pipeline/endnote.py` | Resolves `ADDIN EN.CITE` field codes to plain text by extracting `<DisplayText>` and replacing the field with a simple run. Handles both simple-field and complex-field forms. |
| `src/moore_pipeline/headshots.py` | Normalizes all three source images to sRGB JPEG, then squares-and-frames each on the upper-third vertical center. Uses `tme_template.headshot.frame_headshot_square`. |
| `src/moore_pipeline/cover_snippet.py` | Generates `TME_Moore_2026_cover.docx` using `tme_template` building blocks. Contains Moore-specific data (title, bios, dates, abstract, keywords, DOI) as module constants. |
| `src/build_moore_cover.py` | Entry point that runs the three modules above in sequence. |

## Assumptions and limitations

- **AVIF support.** Pillow 10.4+ reads AVIF natively. If it doesn't, `.venv/bin/pip install pillow-avif-plugin` and import it at the top of `headshots.py`.
- **EndNote binary fields.** Some EndNote installations save fields as base64-encoded binary instead of inline XML. The resolver only handles the XML form. If the Moore manuscript contains binary fields, those citations will be skipped — check the resolved output for any remaining `ADDIN EN.CITE` markers and resolve them manually.
- **Headshot framing is heuristic.** The square crop is biased toward the upper third of the source image, which is usually right for portraits. If it's wrong for a given photo, crop the source image yourself before running the pipeline.

## Where the larger work lives

- Article spec: `../docs/superpowers/specs/2026-04-16-tme-digital-redesign-design.md`
- Pipeline plan: `../docs/superpowers/plans/2026-04-16-moore-article-production.md`
- Template generator: `../template_build/` (produces the reusable template that the Moore article slots into)
- Merge workflow: `MERGE_INSTRUCTIONS.md`
