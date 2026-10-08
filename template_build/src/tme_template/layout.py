"""Page geometry shared by the cover builders and the editor app's fixup.

The masthead and tagline tables span the full page width plus a small bleed
that closes the gap Word leaves at the page edge in Compatibility Mode 14
(the mode python-docx's default template pins). Everything that needs those
numbers imports them from here so a width change happens in one place.
"""
from docx.shared import Inches

PAGE_WIDTH_IN = 8.5
PAGE_HEIGHT_IN = 11.0
BLEED_IN = 0.063
MASTHEAD_LOGO_FRACTION = 0.38      # left (logo) column share of the page width

MASTHEAD_LEFT_WIDTH = Inches(PAGE_WIDTH_IN * MASTHEAD_LOGO_FRACTION)
MASTHEAD_RIGHT_WIDTH = Inches(PAGE_WIDTH_IN * (1 - MASTHEAD_LOGO_FRACTION) + BLEED_IN)
FULL_BLEED_WIDTH = Inches(PAGE_WIDTH_IN + BLEED_IN)
