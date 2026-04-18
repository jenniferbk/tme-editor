# Preparing the Moore article for publication

After running `build_moore_cover.py` you have:
- `TME_Moore_2026_starter.docx` — a complete starter document: cover page (masthead, title, authors with 3-column headshot row, abstract, keywords, author bios, cover footer) + body section with running headers/footer pre-set and a placeholder paragraph.
- `moore_build/intermediate/Moore_resolved.docx` — the Moore manuscript with EndNote citations resolved.

Your goal: produce `TME_Moore_2026.docx` — the complete camera-ready Word file — then export it to `TME_Moore_2026.pdf`.

## Step 1: Open the starter

Open `TME_Moore_2026_starter.docx`. Save As `TME_Moore_2026.docx` in the TME folder.

## Step 2: Paste the Moore body

1. Open `moore_build/intermediate/Moore_resolved.docx`.
2. Select from the start of the body (just after the authors/affiliations block) through the end of the document.
3. Copy (Cmd-C).
4. In `TME_Moore_2026.docx`, navigate to the placeholder paragraph `[Paste Moore article body here ...]` on page 2.
5. Select that placeholder paragraph and delete it.
6. Paste with "Keep Source Formatting" at the now-empty insertion point.

## Step 3: Apply body styles

For each paragraph in the body:
- Main body text: apply **TME Body** from the Styles pane.
- Section headings (e.g., "Conceptual Analysis and Quantitative Reasoning"): apply **TME H1**. After applying H1, add a left paragraph border: 3pt, color `#BA0C2F` (via Design tab or Format > Borders dialog).
- Subsection headings: apply **TME H2**.
- Sub-subsection headings: apply **TME H3**.
- Figure captions (e.g., "Figure 1."): apply **TME Figure Caption**. Style "Figure N." in red Arial bold small caps.
- Table captions: apply **TME Table Caption**.
- Block quotes: apply **TME Block Quote**.
- Pull quotes (if any): apply **TME Pullquote**. Add 2pt red top border and 1pt red bottom border manually, color `#BA0C2F`.
- Footnotes: apply **TME Footnote**.
- Reference entries (after the References heading): apply **TME Reference** to each entry.

## Step 4: Caption figures

The Moore manuscript has 9 figures. For each:
- Ensure the figure is centered on its own line.
- Immediately below, create a caption paragraph: type `Figure N.`, space, then the figure description. Apply **TME Figure Caption**.
- Style "Figure N." in red Arial small caps bold (Format > Font, color `#BA0C2F`, Arial bold, 9.5pt, ALL CAPS).

## Step 5: Save as PDF

1. Save `TME_Moore_2026.docx`.
2. File → Save As → File Format: **PDF** → Save as `TME_Moore_2026.pdf` in the TME folder.
3. Open the PDF in Preview and proofread.

## Troubleshooting

- **Headshots look square, not round.** Right-click each headshot → Format Picture → Crop to Shape → Oval.
- **Citations still look garbled.** Search for `ADDIN` in the document body and replace with the intended citation text.
- **Body text is wrong font/size.** Select all body paragraphs and apply the **TME Body** style.
- **Page numbers missing.** Check that the body section's footer has the `{PAGE}` field. Insert via Insert → Page Number → Bottom of Page if needed.
