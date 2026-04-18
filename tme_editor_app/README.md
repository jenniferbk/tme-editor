# TME Editor App

A web tool for building formatted *The Mathematics Educator* articles from a submitted manuscript. Intended for use by future TME editors who are not expected to know Python or Word styles in depth.

## What it does

1. You upload the submitted manuscript `.docx`.
2. Gemini Flash extracts the title, authors, affiliations, abstract, keywords, and dates automatically.
3. You review and correct anything the LLM got wrong (it will miss things — that's the editor's job).
4. You upload headshot images and pair each one with an author.
5. Click **Build**. The app:
   - Resolves any unrendered EndNote citations in the manuscript.
   - Crops each headshot to a face-centered circle.
   - Generates a TME-formatted starter `.docx` with the cover page, masthead, and body placeholder.
6. Download the starter. Open it in Word, paste the article body into the placeholder (Paste → **Keep Source Formatting**), run the companion styling script, export to PDF.

## Running locally (for development or testing)

```bash
cd /Users/jenniferkleiman/Documents/TME/tme_editor_app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ../template_build -e ../moore_build
export GEMINI_API_KEY=<your-key>
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Deploying

The app is packaged as a Docker image so it can run in any of these environments:

### Option A: UGA-hosted (preferred long-term)

If UGA Libraries or Franklin College provides a small Linux VM or container host:

```bash
# On the VM:
git clone <repo>
cd <repo>
docker build -t tme-editor -f tme_editor_app/Dockerfile .
docker run -d -p 80:8501 -e GEMINI_API_KEY=<key> --restart unless-stopped tme-editor
```

Point a DNS record (e.g. `tme-editor.uga.edu` or a subpath) at the VM.

### Option B: Hugging Face Spaces (free, easy)

Create a new Space of type "Docker". Push this repo. Set `GEMINI_API_KEY` as a Space secret. URL will be `https://<username>-tme-editor.hf.space`.

### Option C: Any PaaS

Same Dockerfile works on Railway, Render, Fly.io, or any provider that runs a Docker image.

## Getting a Gemini API key

1. Go to https://aistudio.google.com/apikey
2. Sign in with a Google account
3. Create an API key (free tier is generous — comfortably covers normal TME volume)
4. Paste into the `GEMINI_API_KEY` environment variable / host secret

## If it breaks

This app depends on:
- **Streamlit** — UI framework. Version bumps occasionally break layouts.
- **google-genai SDK** — Gemini client. Model names and response formats sometimes change.
- **python-docx, Pillow, opencv** — stable, rarely break.

When something breaks, the fallback is always: build the article manually from `TME_Template_2026.docx` following `docs/superpowers/specs/2026-04-16-tme-digital-redesign-design.md`. The app is a time-saver, not a dependency.

## Codebase layout

```
tme_editor_app/
├── app.py                 # Streamlit UI
├── src/
│   ├── extractor.py       # Gemini-based metadata extraction
│   ├── article_starter.py # Generalized starter .docx builder
│   └── pipeline.py        # Orchestrates endnote + headshots + starter
├── requirements.txt
├── Dockerfile
└── README.md
```

Depends on two sibling packages:
- `../template_build/` — the TME style + layout library (`tme_template` Python package)
- `../moore_build/` — the EndNote resolver and headshot prep (`moore_pipeline` Python package)
