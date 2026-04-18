# TME Editor

A hosted web app that turns a submitted mathematics-education manuscript into a
publication-ready proof for *The Mathematics Educator* (TME). Built so that
non-technical editors can run the full formatting pipeline from a browser —
no install, no CLI.

## What it does

Three stages, with a manual Word step in the middle so equations and embedded
objects round-trip cleanly:

1. **Phase 1 — Cover build.** Upload the manuscript + author headshots. Gemini
   Flash extracts the metadata (title, authors, abstract, dates, keywords).
   Review and correct in the UI. App builds a formatted cover page (masthead,
   author cards, abstract, keywords) and hands back a `starter.docx`.
2. **Manual paste step.** Open the starter in Word, paste the article body
   with *Paste Special → Keep Source Formatting*, save.
3. **Phase 2 — Finalize proof.** Upload the populated docx. Gemini classifies
   every paragraph (heading / body / caption / reference / block-quote / list)
   and the fixup battery applies TME styles, centers tables, fixes footnote
   fonts, repairs reference hanging indents, and closes a long list of
   Word-paste gotchas. Download `proof.docx`.

## Repo layout

- `tme_editor_app/` — the Streamlit app itself
- `template_build/` — `tme_template` package (cover, masthead, tagline,
  headers/footers, styles, OOXML helpers). Used by the app and by a CLI
  `build_template.py` that generates a reusable `.docx` template.
- `moore_build/` — `moore_pipeline` package (EndNote citation resolution,
  headshot framing) plus the article-specific one-off scripts used for the
  Spring 2026 Moore article.
- `assets/` — the TME logo (landscape + portrait) used on covers.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY=<your-key>  # get one at https://aistudio.google.com/apikey
streamlit run tme_editor_app/app.py
```

Open http://localhost:8501.

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub.
2. Sign in at https://share.streamlit.io with your GitHub account.
3. *New app* → pick this repo → main file path: `tme_editor_app/app.py`.
4. *Advanced settings* → Secrets. Add:
   ```
   GEMINI_API_KEY = "sk-…"
   ```
   (The app reads the key via `os.environ.get("GEMINI_API_KEY")`; Streamlit
   Cloud surfaces secrets as env vars.)
5. Deploy. The URL will look like `<app-name>.streamlit.app`.

To restrict who can open the app: on the app's settings page, toggle
*Viewer access* → *Only specific people*, and add the editors' email addresses.

## Credits

Built at UGA for TME. Logo © Mathematics Education Student Association.
