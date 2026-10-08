"""Source paragraph styles that name a caption map deterministically, without
waiting on the LLM classifier."""
import apply_styles


def test_caption_like_source_style_names_are_recognised():
    for name in ("Caption", "Figure Caption", "Table Caption", "FigureLabel", "Table Label", "caption"):
        assert apply_styles.is_caption_source_style(name), name
    for name in ("Normal", "TME Body", "Heading 1", "PictureANDLetterLabels", "List Paragraph"):
        assert not apply_styles.is_caption_source_style(name), name


def test_style_name_decides_figure_vs_table_before_text_does():
    assert apply_styles.caption_style_for("Table Caption", "Scoring Rubric") == "TME Table Caption"
    assert apply_styles.caption_style_for("Figure Caption", "Table of values shown") == "TME Figure Caption"
    assert apply_styles.caption_style_for("FigureLabel", "Figure 1") == "TME Figure Caption"


def test_generic_caption_style_falls_back_to_leading_word():
    assert apply_styles.caption_style_for("Caption", "Table 1. Participants") == "TME Table Caption"
    assert apply_styles.caption_style_for("Caption", "Figure 1. A graph") == "TME Figure Caption"
    assert apply_styles.caption_style_for("Caption", "Untitled") == "TME Figure Caption"
