from tme_template.colors import (
    UGA_RED, BLACK, TAGLINE_GRAY, RULE_GRAY,
    LIGHT_PANEL_GRAY, FOOTER_CREAM,
)


def test_uga_red_is_bulldog_red():
    assert UGA_RED == "BA0C2F"


def test_black():
    assert BLACK == "000000"


def test_tagline_gray():
    assert TAGLINE_GRAY == "555555"


def test_rule_gray():
    assert RULE_GRAY == "DDDDDD"


def test_light_panel_gray():
    assert LIGHT_PANEL_GRAY == "F5F5F5"


def test_footer_cream():
    assert FOOTER_CREAM == "FAFAF7"


def test_no_hash_prefix():
    """python-docx shading expects hex without #."""
    assert not UGA_RED.startswith("#")
