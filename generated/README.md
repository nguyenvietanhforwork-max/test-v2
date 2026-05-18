# generated/ — derived dashboard feed and indexes

Everything here is **derived** from `content/` via `scripts/build_index.py`. If lost, regenerate.

## Files

| File | Producer | Consumer |
|---|---|---|
| `index.json` | `scripts/build_index.py` | `apps/dashboard/index.html` (article list + mini-reports) |
| `search-index.json` | `scripts/build_index.py` | Meilisearch loader (optional) |
| `graph.json` | `scripts/build_graph.py` | `apps/dashboard/` graph view (future) |
| `embeddings-ready.json` | `scripts/build_index.py` | `scripts/generate_embeddings.py` queue |

## Shape: `index.json`

```json
{
  "generated_at": "2026-05-18T06:00:00+07:00",
  "schema_version": 1,
  "items": [
    {
      "id": "thutuc-xaydung",
      "topic": "vimo-vn",
      "industry": "phaply",
      "title": "...",
      "desc": "...",
      "author": "Thanh Xuân",
      "source": "vneconomy.vn",
      "published": "2026-05-15",
      "url": "https://...",
      "mini_report": {
        "topic_sentence": "...",
        "bullets": ["...", "..."]
      },
      "report_path": "content/reports/2026-05-15-thutuc-xaydung.md",
      "entities": [],
      "themes": [],
      "signal_score": 0.0,
      "novelty_score": 0.0,
      "prompt_version": "summarization/topic-sentence-bullets@v3",
      "model": "claude-sonnet-4-6"
    }
  ]
}
```

The shape matches the `const ITEMS = [...]` array currently inlined in `apps/dashboard/index.html`, with the additional semantic fields from `schemas/report.schema.json`. Dashboard reads either inlined ITEMS (fallback) or fetches `index.json`.

## Regenerating

```bash
python scripts/build_index.py
python scripts/build_graph.py
python scripts/generate_embeddings.py    # writes to generated/embeddings/*.npy
```

## Versioning

`schema_version` in each file bumps when the consumer-facing shape changes. Bump it, update the dashboard to handle both versions, then ship.
