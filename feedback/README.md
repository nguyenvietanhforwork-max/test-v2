# feedback/ — human preference intelligence infrastructure

Per **ADR-007**, feedback is canonical intelligence — not a feature. This directory is the durable home for:

- Every rating the user gives a report
- Aggregates by prompt version, model, and template
- Datasets ready for prompt-optimization (DPO, preference modeling) training

## Layout

```
feedback/
├── ratings.json         ← append-only stream of every rating
├── inbox/               ← drop preferences-YYYY-MM-DD.json exports here; analyze_feedback.py picks them up
├── analytics/           ← derived aggregates
│   ├── per-prompt-version.json
│   ├── per-model.json
│   └── per-template.json
└── datasets/            ← training-ready datasets
    └── preference-pairs.jsonl
```

## Rating schema

See `schemas/rating.schema.json`. Every rating record carries:

- `rated_at` (ISO timestamp)
- `report_id` (FK to `content/reports/<id>.md`)
- `criteria`: { `data_density`: 1–5, `insight_quality`: 1–5, `writing_style`: 1–5 }
- `length_appropriateness`: "too short" | "just right" | "too long"
- `tags`: free-form list of issues / praise (e.g. "buried lede", "great context")
- `notes`: free-form text
- `prompt_version`: e.g. `summarization/topic-sentence-bullets@v3` — copied from the report's frontmatter
- `model`: e.g. `claude-sonnet-4-6`
- `template_version`: e.g. `intelligence-letter@v2`

## Ingestion paths

1. **Dashboard local export** — user clicks "Export preferences.json" in `apps/dashboard/index.html`, the file lands in their Downloads, they drop it into `feedback/inbox/`. Next `analyze_feedback.py` run picks it up and appends to `ratings.json`.

2. **Dashboard API push** — user clicks the planned "Submit" button → POSTs to `/api/v1/feedback`. API validates against `schemas/rating.schema.json` and appends to `ratings.json` server-side.

Both paths converge on `ratings.json`. The dashboard already implements path #1; path #2 is the next iteration.

## Analysis

```bash
python scripts/analyze_feedback.py
```

Produces:
- `analytics/per-prompt-version.json` — average scores, sample sizes, top tags per prompt version
- `analytics/per-model.json` — same dimensions per model
- `analytics/per-template.json` — same per template
- `datasets/preference-pairs.jsonl` — implicit pairs from same-day ratings (high-score vs. low-score on similar topics) for future DPO training

## What this enables

When the data is rich enough:
- Auto-flag prompt versions whose `insight_quality` average drops below threshold
- Auto-promote prompt versions whose tag profile aligns with user-preferred style
- Generate training data for a small preference model that pre-scores reports before the user sees them
