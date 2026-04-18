# TME Digital Template Generator

Generates `TME_Template_2026.docx`, the reusable Microsoft Word template for *The Mathematics Educator*.

## Why this exists

The journal moved to digital-only in 2026. This folder contains a Python script that produces the Word template from scratch so future editors — or a future maintenance pass — can re-generate the template reliably, without relying on anyone's memory of what Word menus to click.

## To regenerate the template

```bash
cd template_build
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python src/build_template.py
```

Output: `TME_Template_2026.docx` in the parent folder.

## To run tests

```bash
.venv/bin/pytest -v
```

## Where the design lives

`docs/superpowers/specs/2026-04-16-tme-digital-redesign-design.md` — the full design spec. Any change to colors, typography, or layout should be made in the spec first, then reflected in the matching module here:

| Concern | Module |
| --- | --- |
| Colors | `src/tme_template/colors.py` |
| Paragraph styles | `src/tme_template/styles.py` |
| Masthead | `src/tme_template/masthead.py` |
| Tagline | `src/tme_template/tagline.py` |
| Page setup | `src/tme_template/page_setup.py` |
| Headers/footers | `src/tme_template/headers_footers.py` |
| Cover page body | `src/tme_template/cover_page.py` |
| Cover footer | `src/tme_template/cover_footer.py` |
| Front matter pages | `src/tme_template/front_matter.py` |
| OOXML plumbing | `src/tme_template/oxml_helpers.py` |
| Headshot framing | `src/tme_template/headshot.py` |

Each module has an accompanying `tests/test_*.py`.

## Known limitations

- Visual styling of pullquote borders and H1 left-rules requires calling the helper in `oxml_helpers.py` at *paragraph creation time* — they can't live on the paragraph style. Apply them whenever you insert a pullquote or H1 into an article.
- Running footer is currently identical on verso and recto. If you need strict outer-corner page numbers per the spec, flip the `page_on_right` branch in `headers_footers.py`.
- Cambria Math (spec's equation font) depends on Microsoft's math fonts being installed; fall back to STIX Two Math if needed.
- The portrait logo (`tme-logo-portrait.jpg`) is a CMYK JPEG, which python-docx cannot read directly. The build script automatically converts it to sRGB using Pillow before inserting it.

## Future ideas (not implemented)

- A preprocessing CLI that takes a raw manuscript `.docx`, resolves EndNote, places author bios, and emits a template-ready file.
- HTML article pages to complement the PDF (digital-native reading).
