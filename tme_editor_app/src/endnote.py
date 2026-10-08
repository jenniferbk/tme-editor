"""Resolve EndNote ADDIN EN.CITE field codes to plain text.

Word stores EndNote citations as compound fields containing the original EndNote XML.
When the field is "toggled off" or the source Word session didn't have EndNote loaded,
the field stores unrendered XML instead of a resolved citation. This module walks the
OOXML of the document and replaces each such field with its DisplayText.
"""
import html
import re
import shutil
from pathlib import Path

from docx.oxml.ns import qn
from lxml import etree


DISPLAY_TEXT_RE = re.compile(
    r'<DisplayText>(.*?)</DisplayText>',
    re.DOTALL,
)

# The ampersand-encoded variant used inside field codes:
DISPLAY_TEXT_ENCODED_RE = re.compile(
    r'DisplayText&gt;([^&]+)&lt;/DisplayText',
    re.DOTALL,
)


def extract_display_text(addin_body: str) -> str | None:
    """Extract the DisplayText from an ADDIN EN.CITE field body.

    Returns the plain text citation (e.g., "von Glasersfeld (1995)") or None
    if no DisplayText was found.
    """
    # Try the standard XML form first
    m = DISPLAY_TEXT_RE.search(addin_body)
    if m:
        return html.unescape(m.group(1))
    # Try the HTML-entity-encoded form (happens when the field was inside another field)
    m = DISPLAY_TEXT_ENCODED_RE.search(addin_body)
    if m:
        return html.unescape(m.group(1))
    return None


def _unzip(src: Path, dst_dir: Path) -> None:
    import zipfile
    with zipfile.ZipFile(src) as z:
        z.extractall(dst_dir)


def _zip(src_dir: Path, dst: Path) -> None:
    import zipfile
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in src_dir.rglob('*'):
            if p.is_file():
                z.write(p, p.relative_to(src_dir))


def _resolve_in_document_xml(xml_path: Path) -> None:
    """Walk document.xml and replace each fldSimple or complex field with ADDIN EN.CITE
    by a run containing the DisplayText."""
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    tree = etree.parse(str(xml_path))
    root = tree.getroot()

    # Case A: simple fields — <w:fldSimple w:instr="ADDIN EN.CITE ..."><w:r>...</w:r></w:fldSimple>
    for fld in root.findall('.//w:fldSimple', ns):
        instr = fld.get(qn('w:instr')) or ''
        if 'ADDIN EN.CITE' not in instr:
            continue
        display = extract_display_text(instr)
        if display is None:
            continue
        # Replace the whole <w:fldSimple> with a simple <w:r><w:t>display</w:t></w:r>
        parent = fld.getparent()
        new_r = etree.SubElement(parent, qn('w:r'))
        new_t = etree.SubElement(new_r, qn('w:t'))
        new_t.text = display
        # Move new_r to where fld was
        parent.insert(list(parent).index(fld), new_r)
        parent.remove(fld)

    # Case B: complex fields — a begin/end fldChar pair spans multiple runs, with
    # optional inner fields (e.g., ADDIN EN.CITE.DATA) nested between. Structure:
    #   <w:fldChar begin/>
    #   <w:instrText> ADDIN EN.CITE [maybe XML with DisplayText] </w:instrText>
    #   [nested begin/instrText/end for EN.CITE.DATA]
    #   <w:fldChar separate/>
    #   [result runs — the already-rendered citation text]
    #   <w:fldChar end/>
    #
    # For each outer ADDIN EN.CITE field, prefer the DisplayText inside the outer
    # instrText; fall back to keeping the result runs (between separate and outer
    # end) as static text when the instr doesn't carry DisplayText (binary fldData
    # case).
    for para in root.findall('.//w:p', ns):
        children = list(para)
        i = 0
        while i < len(children):
            child = children[i]
            if child.tag != qn('w:r'):
                i += 1
                continue
            fld_char = child.find(qn('w:fldChar'))
            if fld_char is None or fld_char.get(qn('w:fldCharType')) != 'begin':
                i += 1
                continue
            # Walk forward to matching outer 'end', tracking depth. Note outer
            # instrText (depth 1 only) and the index of the outer 'separate'.
            depth = 1
            outer_instr_parts: list[str] = []
            outer_separate_idx = -1
            j = i + 1
            while j < len(children) and depth > 0:
                c = children[j]
                if c.tag != qn('w:r'):
                    j += 1
                    continue
                fld = c.find(qn('w:fldChar'))
                if fld is not None:
                    ftype = fld.get(qn('w:fldCharType'))
                    if ftype == 'begin':
                        depth += 1
                    elif ftype == 'end':
                        depth -= 1
                        if depth == 0:
                            break
                    elif ftype == 'separate' and depth == 1:
                        outer_separate_idx = j
                else:
                    instr_el = c.find(qn('w:instrText'))
                    if instr_el is not None and instr_el.text and depth == 1:
                        outer_instr_parts.append(instr_el.text)
                j += 1
            if depth != 0 or j >= len(children):
                i += 1
                continue
            instr_full = ''.join(outer_instr_parts)
            if 'ADDIN EN.CITE' not in instr_full:
                i = j + 1
                continue
            idx_in_parent = list(para).index(child)
            display = extract_display_text(instr_full)
            field_runs = children[i:j + 1]
            if display is not None:
                for el in field_runs:
                    try: para.remove(el)
                    except ValueError: pass
                new_r = etree.Element(qn('w:r'))
                new_t = etree.SubElement(new_r, qn('w:t'))
                new_t.text = display
                new_t.set(qn('xml:space'), 'preserve')
                para.insert(idx_in_parent, new_r)
            elif outer_separate_idx > 0:
                # No inline DisplayText — preserve the result runs (between
                # outer separate and outer end). Remove only the field
                # structural runs: begin..separate (inclusive) and the final end.
                to_remove = children[i:outer_separate_idx + 1] + [children[j]]
                for el in to_remove:
                    try: para.remove(el)
                    except ValueError: pass
            else:
                i = j + 1
                continue
            children = list(para)
            i = idx_in_parent + 1

    tree.write(str(xml_path), xml_declaration=True, encoding='UTF-8', standalone=True)


def resolve_endnote_citations(src_path: str, dst_path: str) -> None:
    """Take a .docx with unrendered ADDIN EN.CITE fields and produce a new .docx
    where each such field is replaced by its DisplayText."""
    import tempfile
    src, dst = Path(src_path), Path(dst_path)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        _unzip(src, tmp_dir)
        _resolve_in_document_xml(tmp_dir / 'word' / 'document.xml')
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            dst.unlink()
        _zip(tmp_dir, dst)
