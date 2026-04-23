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


def test_removed_constants_are_gone():
    assert not hasattr(colors, "TAGLINE_GRAY")
    assert not hasattr(colors, "RULE_GRAY")
