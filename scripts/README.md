# scripts/ — Python entry points

Per **ADR-004**, every stage of the pipeline has a script wrapper here. These can be run individually without booting Celery, Redis, or the watcher — they compose the same `packages/automation/pipeline/nodes/*` that the worker uses.

## Pipeline order

```
raw/news/**/*.md
    │
    ▼ scripts/crawl.py        (optional — for new sources to add to raw/)
raw/news/**/*.md
    │
    ▼ scripts/clean.py        (normalize → cleaned/)
cleaned/**/*.md
    │
    ▼ scripts/summarize.py    (extract + classify + summarize + score → content/reports/)
content/reports/**/*.md
    │
    ▼ scripts/build_index.py        (markdown → generated/index.json, search-index.json)
    ▼ scripts/build_graph.py        (markdown → generated/graph.json)
    ▼ scripts/generate_embeddings.py (markdown → generated/embeddings/*.npy)
generated/**
    │
    ▼ apps/dashboard/index.html reads generated/index.json
```

## Feedback subloop

```
feedback/inbox/preferences-*.json
    │
    ▼ scripts/analyze_feedback.py
feedback/ratings.json
feedback/analytics/*.json
feedback/datasets/*.jsonl
    │
    ▼ inform iteration on prompts/<bucket>/<name>.md
```

## Scripts

| Script | What it does | Reads | Writes |
|---|---|---|---|
| `crawl.py` | Optional external-source crawler (RSS, web). Currently a stub — Obsidian Web Clipper is the primary ingest path. | external URLs | `raw/news/YYYY-MM-DD/*.md` |
| `clean.py` | Normalize raw clippings: strip boilerplate, extract metadata, dedupe. | `raw/` | `cleaned/` |
| `summarize.py` | Run extract → classify → summarize → score on cleaned docs. Writes intelligence reports. | `cleaned/`, `prompts/` | `content/reports/` |
| `build_index.py` | Walk `content/` and emit the dashboard's data feed. | `content/` | `generated/index.json`, `generated/search-index.json`, `generated/embeddings-ready.json` |
| `build_graph.py` | Build the entity / theme graph from report frontmatter. | `content/reports/`, `content/wiki/entities/` | `generated/graph.json` |
| `generate_embeddings.py` | Generate embeddings for any report listed in `generated/embeddings-ready.json`. | `generated/embeddings-ready.json`, `content/reports/` | `generated/embeddings/*.npy` |
| `analyze_feedback.py` | Ingest `feedback/inbox/`, append to `feedback/ratings.json`, compute aggregates. | `feedback/inbox/`, `feedback/ratings.json` | `feedback/ratings.json`, `feedback/analytics/`, `feedback/datasets/` |
| `cleanup-legacy.ps1` | One-shot v3 restructure cleanup script (PowerShell, Windows). Moves retired systems to `legacy/`, deletes regeneratable junk. See `MIGRATION.md`. | repo | `legacy/`, deletes node_modules/, etc. |

## Running

All Python scripts assume `pip install -r requirements.txt` (TBD — derive from `packages/automation/pyproject.toml` for now).

```bash
# Single-shot daily pipeline:
python scripts/clean.py
python scripts/summarize.py --date 2026-05-18
python scripts/build_index.py
python scripts/build_graph.py
# Now refresh the dashboard.

# Process new feedback:
python scripts/analyze_feedback.py
```

## Configuration

Scripts read the same `.env` as `apps/api/` and `packages/automation/`. Key vars:

- `ANTHROPIC_API_KEY` — for summarize.py, generate_embeddings.py (with model swap)
- `OPENAI_API_KEY` — for generate_embeddings.py
- `EMBEDDING_MODEL` — default `text-embedding-3-large`
- `DEFAULT_MODEL` — default `claude-sonnet-4-6`

See `.env.example`.
