"""Assert the deliberate 5-step grayscale palette is present with correct values."""
import re

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


def test_palette_values_are_six_hex_digits():
    names = [n for n in dir(colors) if n.isupper()]
    assert names
    for n in names:
        assert re.fullmatch(r"[0-9A-Fa-f]{6}", getattr(colors, n)), n
