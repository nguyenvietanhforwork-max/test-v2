---
title: Architecture Decisions — Atlas Hybrid Intelligence Platform
type: ADR
phase: 2
created: 2026-05-18
maintainer: Albert (nguyenvietanhforwork@gmail.com)
status: accepted
supersedes:
  - "(prior implicit decisions in apps/web, intelligence-platform/, infra/k8s/)"
---

# Architecture Decisions — Phase 2

This document records the **accepted architectural decisions** that drive Phases 3–9 of the autonomous restructure. Decisions follow the format: *Context → Decision → Consequences*.

---

## ADR-001 — Hybrid content/data plane (Research Wiki ⊂ Intelligence Platform)

**Context.** The existing `CLAUDE.md` described a generic "Research Wiki" with `raw/`, `wiki/`, `outputs/`. The actual repository is the much larger Atlas Intelligence Platform. The user chose neither — instead, a hybrid: Research Wiki is preserved *as a subsystem* of the broader platform.

**Decision.** Adopt this top-level layout:

```
project/
├── apps/
│   ├── dashboard/          ← single-file canonical UI (news-dashboard-v2.html)
│   └── api/                ← FastAPI (kept, simplified)
├── content/                ← canonical markdown intelligence artifacts (HYBRID hook)
│   ├── reports/            ← daily/weekly intelligence reports (was: Processed/)
│   ├── wiki/               ← Research Wiki — concepts, entities, sources (was: wiki/)
│   ├── _templates/         ← markdown templates
│   └── README.md           ← explains the hybrid: wiki + reports = content
├── raw/                    ← UNCHANGED — immutable internet archive
├── cleaned/                ← NEW — normalized intermediates between raw and content
├── generated/              ← NEW — derived artifacts the dashboard reads
│   ├── index.json
│   ├── search-index.json
│   ├── graph.json
│   └── embeddings-ready.json
├── feedback/               ← NEW — human preference intelligence
│   ├── ratings.json
│   ├── analytics/
│   └── datasets/
├── prompts/                ← NEW — modular prompt architecture
│   ├── system/
│   ├── extraction/
│   ├── summarization/
│   ├── scoring/
│   ├── formatting/
│   └── evaluation/
├── scripts/                ← NEW — consolidated pipeline entry points
├── schemas/                ← NEW — JSON schemas for raw/report/rating/semantic
├── packages/               ← KEEP — agents/, automation/, shared/
├── infra/docker/           ← KEEP — Dockerfiles for api/worker/watcher/pdf
├── logs/                   ← NEW — runtime logs
├── legacy/                 ← NEW — archived retired systems
└── docs/                   ← KEEP — architecture/data-flow/api/deployment docs
```

**Consequences.**
- `raw/` and `wiki/` keep their AGENTS.md-defined semantics. No filename changes inside.
- `content/wiki/` is **the same physical folder** as `wiki/` accessed via the new conceptual name. We document the alias rather than move ~35+ wikilinked notes (which would break every `[[link]]`). Pragmatic: `content/` becomes a *view* over existing folders.
- `Processed/` is renamed/moved to `content/reports/` (this is safe — few inbound links).
- `cleaned/`, `generated/`, `feedback/`, `prompts/`, `scripts/`, `schemas/`, `logs/`, `legacy/` are created from scratch.

---

## ADR-002 — `news-dashboard-v2.html` is the canonical dashboard

**Context.** Four+ dashboard implementations co-exist (`apps/web/` Next.js, `intelligence-platform/apps/dashboard/`, root `index.html`, `news-dashboard-v2.html`, `news-dashboard-soulslab.html`, `demo/dashboard.html`, three `outputs/*-dashboard.html`, five `offline dashboard trial/*`). The Next.js app is the most engineered; the v2 single-file is the most product-realized (VnEconomy editorial styling, inlined article corpus, built-in 4-criteria rating, preferences export, Vercel deploy hook).

**Decision.** `news-dashboard-v2.html` is canonical. Copy to `apps/dashboard/index.html` and make Vercel serve `apps/dashboard/` as a static site. Every other dashboard → `legacy/`.

**Consequences.**
- No Node/Next/pnpm build step on the critical path.
- Vercel config simplifies to a static deploy (`outputDirectory: apps/dashboard`).
- The dashboard's 4-criteria rating + `preferences.json` export becomes the canonical feedback ingest pattern (ADR-007).
- Article data is currently inlined as `const ITEMS = [...]`. Externalization to `content/*.md` + `generated/index.json` is Phase 5 work; the inlined fallback keeps the dashboard operational throughout the migration.

---

## ADR-003 — `apps/api/` is the canonical FastAPI backend

**Context.** Two parallel FastAPI implementations (`apps/api/` and `intelligence-platform/apps/api/`).

**Decision.** `apps/api/` is canonical. Aggressive simplification (per spec "remove enterprise abstraction, premature scalability, fake patterns") happens iteratively. Responsibilities:
- `GET /api/v1/news` — list with filters
- `GET /api/v1/reports` — list + `[id]` detail (markdown + PDF)
- `GET /api/v1/search` — full-text + semantic (Meili + pgvector)
- `GET /api/v1/entities`, `/graph` — semantic infrastructure
- `WS /ws/stream` — real-time pipeline events
- **`POST /api/v1/feedback`** — NEW per ADR-007, ingest from dashboard's preferences export

**Consequences.** `intelligence-platform/apps/api/` retires. `apps/api/Procfile`, `railway.json` retire. `render.yaml` (Render) is the prod target.

---

## ADR-004 — `packages/automation/` is the canonical pipeline

**Context.** Three pipeline implementations: `packages/automation/` (LangGraph + Celery + watchdog), `intelligence-platform/services/{ingestion,workers,agents}` (Celery + n8n), root-level scripts.

**Decision.** `packages/automation/` is canonical. LangGraph state machine: `extract → classify → summarize → embed → persist → publish`. **Plus** `scripts/` directory exposes simple Python entry points (`crawl.py`, `clean.py`, `summarize.py`, `build_index.py`, `analyze_feedback.py`, `build_graph.py`, `generate_embeddings.py`) that wrap or compose the packages/automation logic — so the user can run any pipeline step by hand without booting Celery.

**Consequences.** `intelligence-platform/services/` retires. Root `process_news.py`, `generate.py`, `process_news_agent.py` retire after their content is hoisted into `packages/automation/` (if not already present) and `scripts/` wrappers exist.

---

## ADR-005 — Deployment: Vercel (static) + Render (API) + docker-compose (local dev)

**Context.** Five active deployment targets: `vercel.json`, `render.yaml`, `fly.toml`, `infra/k8s/`, `intelligence-platform/infra/railway/`.

**Decision.** Three paths total — one per environment, no alternatives:
- **Local dev:** `docker-compose.yml` (single-command full stack)
- **Production frontend:** `vercel.json` configured to serve `apps/dashboard/` as static
- **Production backend:** `render.yaml` (api + worker + beat + pdf services)

**Consequences.** `fly.toml`, `infra/k8s/`, `intelligence-platform/infra/railway/`, `apps/api/Procfile`, `apps/api/railway.json` all retire. Spec explicitly forbids Kubernetes; this also resolves that.

---

## ADR-006 — Markdown is canonical; DB/indexes are derived

**Context.** The spec mandates: "Markdown reports are the canonical intelligence layer. Database systems support analytics, search, semantic enrichment... but the intelligence reports themselves remain human-readable canonical artifacts."

**Decision.** Reports live as `content/reports/YYYY-MM-DD-*.md` with full YAML frontmatter (entities, themes, scores, embeddings ref). Postgres / Meilisearch / pgvector are **derived** from markdown via `scripts/build_index.py`. Losing the DB never loses the product — re-run `build_index.py` on `content/` and the system rehydrates.

**Consequences.**
- `generated/index.json` is the dashboard's data feed, built from `content/`.
- The DB schema mirrors the markdown schema, not the other way around.
- Reports must always carry source attribution back to `raw/` paths (already a vault invariant per AGENTS.md).

---

## ADR-007 — Feedback is canonical intelligence (not a feature)

**Context.** The v2 dashboard already collects 4-criteria ratings + tags + length preferences + free-text notes and exports `preferences.json`. Per spec: "Feedback is not a simple likes/dislikes feature. It is human preference intelligence infrastructure."

**Decision.** Formalize:
- `feedback/ratings.json` — accumulated ratings, append-only schema
- `feedback/analytics/` — derived aggregates (per-prompt-version, per-model, per-template)
- `feedback/datasets/` — exported datasets for future prompt-optimization training
- `schemas/rating.schema.json` — JSON Schema constraining ratings (must include `prompt_version`, `model`, `template_version`, `report_id`, criteria scores, tags, free-form notes, timestamp)
- New API endpoint `POST /api/v1/feedback` — ingests the dashboard's preferences.json
- The dashboard's `exportPreferences()` function gets a sibling `submitPreferences()` that POSTs to the API instead of downloading

**Consequences.** Prompt-optimization-ready architecture. Every rating is traceable to the prompt+model that produced the rated content.

---

## ADR-008 — Modular prompts, never monolithic

**Context.** Spec mandates modular prompt architecture.

**Decision.** `prompts/` is the canonical prompt library:
- `prompts/system/identity.md` — agent identity, voice, values
- `prompts/extraction/extract-entities.md`, `extract-claims.md` — extraction stage prompts
- `prompts/summarization/topic-sentence-bullets.md` — the v2 dashboard's editorial pattern formalized
- `prompts/scoring/signal-novelty.md` — signal/novelty/relevance scoring
- `prompts/formatting/intelligence-letter.md` — VnEconomy-style editorial formatting
- `prompts/evaluation/quality-rubric.md` — used by `feedback/` to auto-grade reports

Every prompt file has frontmatter: `version`, `model`, `created`, `last_updated`, `evaluation_dataset`. The pipeline records the prompt version used for every generation in the report's frontmatter.

**Consequences.** Prompt evolution is versionable and the feedback loop is wired to specific versions.

---

## ADR-009 — Semantic readiness without premature embeddings

**Context.** Spec says: "Every report schema should support entities, themes, topics, semantic tags, related reports, signal scores, novelty scores, embeddings references, graph relationships, source attribution, confidence scoring. Even if embeddings are not fully implemented yet."

**Decision.** `schemas/report.schema.json` and `schemas/semantic.schema.json` define the full semantic surface today. The pipeline writes those fields even when downstream consumers (embeddings, graph, related-reports) aren't fully built yet. `scripts/generate_embeddings.py` and `scripts/build_graph.py` exist as stubs that consume the schema-conformant frontmatter when activated.

**Consequences.** Zero schema migration required when embeddings/graph come online. The current dashboard ignores fields it doesn't render yet.

---

## ADR-010 — Anti-overengineering guardrails (no K8s, no microservices, no fake abstractions)

**Decision.** Permanently retired from the canonical architecture:
- Kubernetes (infra/k8s/)
- CQRS / event sourcing
- Service mesh
- Multi-region infra
- Microservices fragmentation (workers and watcher are *processes*, not services)
- "Enterprise" repository / abstraction hierarchies
- Redis as anything beyond Celery broker + Pub/Sub for WS fanout

Anything reintroducing those patterns is auto-rejected. Every abstraction must answer "does this improve intelligence quality and maintainability?"

---

## ADR-011 — `legacy/` is the canonical archive; nothing is destroyed

**Decision.** All retired systems move to `legacy/<category>/` with a `legacy/README.md` manifest. `node_modules`, `__pycache__`, `.next`, `dist`, `.venv` are regeneratable — those are deleted, not archived. Everything human-written is preserved.

**Consequences.** Recovery from any archive is `git mv legacy/X/ X/`. No code is ever lost.

---

## Phase 2 status: complete
Phase 3 (legacy isolation) is next — scripted, user-reviewable execution.
