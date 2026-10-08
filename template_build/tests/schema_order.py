"""Walk every w:pPr, w:tblPr and w:tcPr under an element and report children
that are out of ECMA-376 order. The sequences are the ones python-docx uses
internally (docx/oxml/text/parfmt.py and docx/oxml/table.py, 1.2.0)."""
from docx.oxml.ns import qn

PPR_SEQ = (
    "w:pStyle", "w:keepNext", "w:keepLines", "w:pageBreakBefore", "w:framePr",
    "w:widowControl", "w:numPr", "w:suppressLineNumbers", "w:pBdr", "w:shd",
    "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap",
    "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN",
    "w:bidi", "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind",
    "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc",
    "w:textDirection", "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl",
    "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange",
)
TBLPR_SEQ = (
    "w:tblStyle", "w:tblpPr", "w:tblOverlap", "w:bidiVisual",
    "w:tblStyleRowBandSize", "w:tblStyleColBandSize", "w:tblW", "w:jc",
    "w:tblCellSpacing", "w:tblInd", "w:tblBorders", "w:shd", "w:tblLayout",
    "w:tblCellMar", "w:tblLook", "w:tblCaption", "w:tblDescription",
    "w:tblPrChange",
)
TCPR_SEQ = (
    "w:cnfStyle", "w:tcW", "w:gridSpan", "w:hMerge", "w:vMerge", "w:tcBorders",
    "w:shd", "w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign",
    "w:hideMark", "w:headers", "w:cellIns", "w:cellDel", "w:cellMerge",
    "w:tcPrChange",
)
_SEQS = {qn("w:pPr"): PPR_SEQ, qn("w:tblPr"): TBLPR_SEQ, qn("w:tcPr"): TCPR_SEQ}


def _local(tag):
    return tag.split("}")[-1]


def order_violations(root) -> list[str]:
    bad = []
    for tag, seq in _SEQS.items():
        rank = {qn(t): i for i, t in enumerate(seq)}
        for el in root.iter(tag):
            ranks = [rank[c.tag] for c in el if c.tag in rank]
            if ranks != sorted(ranks):
                bad.append(f"{_local(el.tag)}: " + " ".join(_local(c.tag) for c in el))
    return bad


def document_violations(doc) -> list[str]:
    roots = [doc.element.body]
    for s in doc.sections:
        for part in (s.header, s.footer, s.even_page_header, s.even_page_footer):
            if not part.is_linked_to_previous:
                roots.append(part._element)
    out = []
    for r in roots:
        out.extend(order_violations(r))
    return out
