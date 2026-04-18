# moore-pipeline

Reusable pipeline helpers used by the TME editor app. Each module stands alone;
the app imports them by name.

| Module | What it does |
|---|---|
| `moore_pipeline.endnote` | Walks a `.docx` XML and resolves inline `ADDIN EN.CITE` fields (handles nested fields, falls back to preserving result runs when DisplayText isn't inline). |
| `moore_pipeline.headshots` | Wrapper around `tme_template.headshot.frame_headshot_square` that prepares framed portraits from arbitrary input images. |
| `moore_pipeline.moore_starter` | A one-off example using the pipeline to build the Moore-article starter. Not used by the app. |
| `moore_pipeline.cover_snippet` | Earlier standalone cover-page builder; kept for reference. |

Install from the repo root:

```
pip install ./moore_build
```

or in editable dev mode:

```
pip install -e ./moore_build
```
