"""Generate a standalone .docx containing only the Moore cover-page content."""
from pathlib import Path
from typing import Dict

from docx import Document

from tme_template.masthead import MastheadData, add_masthead
from tme_template.tagline import add_tagline_strip
from tme_template.cover_page import AuthorEntry, CoverData, add_research_article_cover
from tme_template.cover_footer import add_cover_footer
from tme_template.styles import (
    register_body_style, register_title_style,
    register_heading_styles, register_remaining_styles,
)
from tme_template.page_setup import configure_page_setup


REPO_ROOT = Path(__file__).resolve().parents[3]
LOGO_H = REPO_ROOT / "assets" / "tme-logo.jpg"


# Author bios (verbatim from the spec — see
# docs/superpowers/specs/2026-04-16-tme-digital-redesign-design.md §"Moore article — production tasks")
MOORE_BIO = (
    "Kevin C. Moore is a Professor of Mathematics Education at University of Georgia. "
    "His primary research focuses on quantitative reasoning with attention to foundational "
    "shifts in pre-service teachers' mathematical meanings. Dr. Moore's research informs the "
    "design of teacher preparation programs and professional development initiatives, "
    "alternative and novel approaches to major mathematical ideas, and avenues to support "
    "students' covariational and quantitative reasoning."
)
YASUDA_BIO = (
    "Sohei Yasuda is a graduate student at the University of Georgia. His primary research "
    "focuses on the human aspect of mathematics and mathematics education research. His "
    "research informs the design of multivariable calculus instruction that embraces "
    "students' mathematics."
)
WONG_BIO = (
    "Webster Wong is a graduate student at the University of Georgia. His research interests "
    "include undergraduate mathematics curriculum materials."
)

ABSTRACT = (
    "In this paper, we present a conceptual analysis for integration by substitution that "
    "centers major ideas of quantitative reasoning, including accumulation rates, "
    "relationships between measures and unit magnitudes, and the multiplicative dependency "
    "of quantities. Our centering of these ideas enables integration by substitution to "
    "occur through coordinating accumulation rates and intervals to reconstruct a desired "
    "integral structure. Our approach was inspired by the conceptual analysis provided by "
    "Jones and Fonbuena (2024), and thus we compare our approach with theirs throughout in "
    "order to highlight similarities and differences between the two. We close by "
    "acknowledging that a conceptual analysis is only as good as its use in working to "
    "support learning and thus call for future work that transitions the analysis to work "
    "with students."
)

KEYWORDS = [
    "Conceptual Analysis",
    "Integration by Substitution",
    "Quantitative Reasoning",
    "Accumulation",
]

CITATION_APA = (
    "Moore, K. C., Yasuda, S., & Wong, W. (2026). Integration by substitution: An emergent "
    "quantitative reasoning approach to u-substitution. The Mathematics Educator, 34(1), 1–24."
)


def build_moore_cover_snippet(*, out_path: Path, headshots: Dict[str, Path]) -> None:
    """Generate a standalone .docx containing only the Moore cover-page content:
    masthead, tagline, title, authors, affiliations, corresponding-author line, dates,
    abstract, keywords, author block with headshots + bios, and the cover footer.

    headshots must be a dict with keys 'moore', 'yasuda', 'wong' mapping to the framed
    JPG files (output of prepare_all_headshots).
    """
    doc = Document()
    configure_page_setup(doc)
    register_body_style(doc)
    register_title_style(doc)
    register_heading_styles(doc)
    register_remaining_styles(doc)

    # Masthead
    add_masthead(doc, MastheadData(
        article_type="RESEARCH ARTICLE",
        volume=34, number=1, year=2026, pages="1–24",
        doi="doi.org/10.xxxxx/tme.2026.34.1.01",
        issn_print="1062-9017",
        issn_online="2331-4451",
        logo_path=str(LOGO_H),
    ))
    add_tagline_strip(doc)

    # Cover page body with the three authors
    add_research_article_cover(doc, CoverData(
        title=(
            "Integration by Substitution: An Emergent Quantitative Reasoning Approach "
            "to U-Substitution"
        ),
        authors=[
            AuthorEntry(
                name="Kevin C. Moore", affiliation_num=1,
                role=None, bio=MOORE_BIO,
                headshot_path=str(headshots["moore"]),
                corresponding=True, email="kvcmoore@uga.edu",
            ),
            AuthorEntry(
                name="Sohei Yasuda", affiliation_num=1,
                role=None, bio=YASUDA_BIO,
                headshot_path=str(headshots["yasuda"]),
            ),
            AuthorEntry(
                name="Webster Wong", affiliation_num=1,
                role=None, bio=WONG_BIO,
                headshot_path=str(headshots["wong"]),
            ),
        ],
        affiliations=["Department of Mathematics and Science Education, University of Georgia"],
        dates={
            "Received": "Dec 3, 2024",
            "Revised": "Jan 22, 2025",
            "Accepted": "Apr 3, 2025",
            "Published": "Apr 2026",
        },
        abstract=ABSTRACT,
        keywords=KEYWORDS,
    ))

    # Cover footer goes in the section footer slot (not the body)
    add_cover_footer(
        doc.sections[0],
        citation=CITATION_APA,
        license_text="CC BY 4.0",
        copyright_text="© 2026 The Authors",
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
