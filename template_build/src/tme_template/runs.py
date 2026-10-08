"""Run helpers shared by the cover builders."""
from docx.shared import Pt, RGBColor

from tme_template.colors import UGA_RED


def add_red_run(paragraph, text: str, *, size_pt: float, bold: bool = False, name: str = "Arial"):
    """Append a UGA-red run (Arial by default) and return it."""
    r = paragraph.add_run(text)
    r.font.name = name
    r.font.size = Pt(size_pt)
    r.font.bold = bold
    r.font.color.rgb = RGBColor.from_string(UGA_RED)
    return r
