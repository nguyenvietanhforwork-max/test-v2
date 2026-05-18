# Atlas — System Architecture (Hybrid AI-Native Intelligence Platform)

> Status: **v3 — post-restructure (2026-05-18)**. Supersedes the v2 Atlas architecture and the parallel `intelligence-platform/` monorepo (both archived in `legacy/`).

The platform is an **AI-native intelligence infrastructure** that turns a daily flow of raw clippings into executive-grade, semantically-enriched intelligence reports. It combines four mental models:

```
Obsidian Vault  +  Executive Intelligence Feed  +  AI Research Infrastructure  +  Human Feedback Loop
```

The architecture is markdown-canonical: the intelligence reports themselves are human-readable Markdown files. Postgres, Meilisearch, pgvector, and the JSON indexes in `generated/` are all *derived* from those files and can be rebuilt at any time by re-running `scripts/build_index.py`.

---

## Top-level layout

```
project/
├── apps/
│   ├── dashboard/          ← canonical single-file dashboard (news-dashboard-v2 lineage)
│   │   └── index.html      ← VnEconomy-style editorial UI, inlined data + Vercel sync
│   └── api/                ← FastAPI: REST + WebSocket
│
├── content/                ← CANONICAL intelligence artifacts (human-readable markdown)
│   ├── reports/            ← daily + weekly intelligence reports (was: Processed/)
│   ├── wiki/               ← Research Wiki — concepts, entities, sources (= wiki/)
│   └── _templates/         ← markdown templates
│
├── raw/                    ← IMMUTABLE internet archive (Obsidian Web Clipper drops here)
├── cleaned/                ← normalized intermediates between raw/ and content/
├── generated/              ← DERIVED dashboard feed
│   ├── index.json
│   ├── search-index.json
│   ├── graph.json
│   └── embeddings-ready.json
│
├── feedback/               ← HUMAN PREFERENCE INTELLIGENCE
│   ├── ratings.json        ← append-only ratings stream
│   ├── analytics/          ← per-prompt-version / per-model aggregates
│   └── datasets/           ← exported training-ready datasets
│
├── prompts/                ← MODULAR prompt library (versioned)
│   ├── system/             ← identity, voice
│   ├── extraction/         ← entities, claims, structured-data
│   ├── summarization/      ← topic-sentence + bullets
│   ├── scoring/            ← signal / novelty / confidence
│   ├── formatting/         ← intelligence-letter (editorial style)
│   └── evaluation/         ← quality rubric for feedback grading
│
├── scripts/                ← Python entry points (no Celery required to run)
│   ├── crawl.py
│   ├── clean.py
│   ├── summarize.py
│   ├── build_index.py
│   ├── analyze_feedback.py
│   ├── build_graph.py
│   ├── generate_embeddings.py
│   └── cleanup-legacy.ps1
│
├── schemas/                ← JSON Schema for raw / report / rating / semantic
│
├── packages/               ← shared internal libraries
│   ├── agents/             ← LLM client wrappers, agent definitions, tools
│   ├── automation/         ← LangGraph + Celery + watchdog (production pipeline)
│   └── shared/             ← cross-package types
│
├── infra/docker/           ← Dockerfiles (api, worker, watcher, pdf)
├── logs/                   ← runtime logs
│
├── legacy/                 ← archived retired systems (intelligence-platform/, nextjs-dashboard/, k8s/, etc.)
└── docs/                   ← architecture, data-flow, api, deployment, ui-design-system
```

---

## Data plane (markdown is source of truth)

```
            Obsidian Web Clipper
                    │
                    ▼
            raw/news/*.md   ◀── IMMUTABLE
                    │
                    ▼ (fsevent → packages/automation/watcher)
            cleaned/*.md     ← normalized text, extracted metadata
                    │
                    ▼ (LangGraph: extract → classify → summarize → embed → persist)
            content/reports/YYYY-MM-DD-*.md   ← CANONICAL intelligence artifacts
            content/wiki/**/*.md              ← concept, entity, source pages updated
                    │
                    ▼ (scripts/build_index.py)
            generated/index.json              ← dashboard reads this
            generated/search-index.json       ← Meilisearch hydrates from this
            generated/graph.json              ← entity graph
            generated/embeddings-ready.json   ← embedding queue
                    │
                    ▼
            apps/dashboard/index.html         ← renders generated/index.json
                    │
                    ▼ (user rates a report)
            feedback/ratings.json (append)    ← POST /api/v1/feedback OR exportPreferences()
                    │
                    ▼ (scripts/analyze_feedback.py)
            feedback/analytics/*.json         ← per-prompt-version aggregates
            feedback/datasets/*.jsonl         ← training-ready data
```

Every step is idempotent. Losing the DB or `generated/` never loses the product — re-run `scripts/build_index.py` over `content/`.

---

## Control plane

- **Trigger:** filesystem event on `raw/news/` (watchdog) **or** manual `python scripts/crawl.py`
- **Bus:** Redis Streams (`ingest`, `enrich`, `report`) — only when Celery worker is running
- **Orchestrator:** LangGraph state machine in `packages/automation/pipeline/graph.py`
- **Scheduler:** Celery Beat — daily 06:00 ICT report build, weekly 07:00 Monday synthesis
- **Realtime fanout:** Redis Pub/Sub → FastAPI WebSocket → dashboard

For one-off processing the user runs Python scripts directly — no Celery required. The pipeline composes cleanly out of `packages/automation/pipeline/nodes/*`.

---

## Service inventory

| Service | Port | Required? | Responsibility |
|---|---|---|---|
| `dashboard` (static HTML) | 3000 (vercel) | yes | Single-file UI, reads `generated/index.json` |
| `api` (FastAPI) | 8000 | yes | REST + WebSocket gateway, feedback ingest |
| `worker` (Celery + LangGraph) | — | only for live pipeline | AI pipeline execution |
| `watcher` (watchdog) | — | only for live ingest | Vault file events → Redis Stream |
| `pdf` (Puppeteer + Node) | 4000 | only for PDF rendering | Headless PDF microservice |
| `postgres` (pgvector) | 5432 | only for DB-backed queries | Relational + vector storage |
| `redis` | 6379 | only for live pipeline | Cache, queue, pub/sub |
| `meili` | 7700 | only for live search | Full-text + hybrid search |

**Minimum viable stack:** `dashboard` (static) + `api`. The dashboard works standalone with inlined data; the API only matters when feedback ingestion or live search is active.

---

## Semantic schema (every report carries)

Defined in `schemas/report.schema.json`. Frontmatter on every `content/reports/*.md`:

```yaml
---
id: report-2026-05-18-001
type: report
date: 2026-05-18
title: ...
sources: ["raw/news/2026-05-18/foo.md", ...]
entities: [{ name: "Vinhomes", ticker: "VHM", confidence: 0.92 }, ...]
themes: ["vimo-vn", "real-estate"]
topics: ["land-pricing-reform", "FDI-flows"]
tags: [...]
related_reports: ["report-2026-05-17-003", ...]
signal_score: 0.87        # how much this changes someone's view
novelty_score: 0.62       # how non-obvious
confidence: high
embeddings_ref: generated/embeddings/report-2026-05-18-001.npy
prompt_version: summarize/topic-sentence-bullets@v3
model: claude-sonnet-4-6
template_version: intelligence-letter@v2
generated_at: 2026-05-18T06:00:00+07:00
---
```

All of these fields are written by the pipeline today, even when downstream consumers (embeddings, graph, related-reports) are not yet activated. **Zero schema migration** when those come online.

---

## Feedback architecture

The dashboard collects 4 ratings per report (data density, insight quality, writing style, length appropriateness), free-text tags, and notes. Submission via either:

1. **Local export** — `exportPreferences()` writes `preferences-YYYY-MM-DD.json` to user's machine
2. **API push** — `submitPreferences()` POSTs to `/api/v1/feedback`, server appends to `feedback/ratings.json`

`scripts/analyze_feedback.py` aggregates ratings by `prompt_version` + `model` + `template_version` and writes:
- `feedback/analytics/per-prompt-version.json`
- `feedback/analytics/per-model.json`
- `feedback/datasets/preference-pairs.jsonl` (for future DPO/preference-optimization training)

---

## Deployment

| Environment | Stack | Config |
|---|---|---|
| Local dev | docker compose up — full 8-service stack | `docker-compose.yml` |
| Production frontend | Vercel static (serves `apps/dashboard/`) | `vercel.json` |
| Production backend | Render (api + worker + beat + pdf) | `render.yaml` |

**Forbidden** (by ADR-010, retired to `legacy/`): Kubernetes, Fly.io alternative, Railway alternative, n8n orchestration, service mesh, multi-region.

---

## Anti-patterns (rejected by design)

Per ADR-010, the following are **never** reintroduced:
- Microservices fragmentation — workers are processes inside the monorepo
- CQRS / event sourcing
- Service mesh / sidecars
- Kubernetes
- Repository hierarchies / "enterprise" abstraction patterns
- Premature scaling for hypothetical millions of users
- Redis used as anything beyond queue + pub/sub

Every new abstraction must answer: **"Does this improve intelligence quality and maintainability?"** If not, it does not ship.

---

## Document map

- `outputs/audit-2026-05-18.md` — Phase 1 audit with fork resolutions
- `outputs/architecture-decisions-2026-05-18.md` — full ADR set (ADR-001 … ADR-011)
- `outputs/restructure-2026-05-18.md` — pre-existing restructure analysis
- `MIGRATION.md` — what moved where, with cleanup-legacy.ps1 instructions
- `CLAUDE.md` — operational instructions for AI agents
- `AGENTS.md` — vault charter (raw/ immutability, naming, schemas)
- `docs/architecture.md`, `docs/data-flow.md`, `docs/api.md`, `docs/ui-design-system.md`, `docs/deployment.md`
