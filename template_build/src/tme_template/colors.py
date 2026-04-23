"""Deliberate color palette for TME digital template.

Hex strings WITHOUT leading #, as required by python-docx shading API.
See docs/superpowers/specs/2026-04-23-tme-template-post-moore-proof-design.md
§"Deliberate 5-step grayscale palette".
"""

# Accents
UGA_RED = "BA0C2F"
BLACK = "000000"

# 5-step grayscale (deliberate; do not add new shades without updating the spec)
INK = "111111"             # Title, H1, H2, H3, body text
BLOCKQUOTE_INK = "333333"  # TME Block Quote only — intentionally a touch lighter than body
TEXT_MUTED = "444444"      # captions, footnote, cover-footer text, page number, issue credit
META = "777777"            # dates, affiliations, tagline italic, running-footer meta,
                           # front-matter role labels
LINE = "BBBBBB"            # cover rules, date separators, footer top rule

# Panels (non-text)
LIGHT_PANEL_GRAY = "F5F5F5"  # tagline strip background
FOOTER_CREAM = "FAFAF7"      # cover footer background
