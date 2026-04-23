"""Assert the deliberate 5-step grayscale palette is present with correct values."""
from tme_template import colors


def test_palette_grays_defined():
    assert colors.INK == "111111"
    assert colors.BLOCKQUOTE_INK == "333333"
    assert colors.TEXT_MUTED == "444444"
    assert colors.META == "777777"
    assert colors.LINE == "BBBBBB"


def test_palette_accents_defined():
    assert colors.UGA_RED == "BA0C2F"
    assert colors.BLACK == "000000"
    assert colors.LIGHT_PANEL_GRAY == "F5F5F5"
    assert colors.FOOTER_CREAM == "FAFAF7"


def test_deprecation_aliases_resolve_to_new_palette():
    # Deprecated aliases are kept through the migration so tagline.py and any
    # other importer keeps working until Task 12 removes each usage. Final
    # removal happens at the end of the migration (Task 12h).
    assert colors.TAGLINE_GRAY == colors.META
    assert colors.RULE_GRAY == colors.LINE
