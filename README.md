# Atlas — AI-Native Intelligence Platform

> **Codename:** Atlas — v3 (post-restructure 2026-05-18).
> The platform turns daily news clippings into executive-grade intelligence reports, semantically enriched, with a tight human-feedback loop.

```
Obsidian Vault  +  Executive Intelligence Feed  +  AI Research Infrastructure  +  Human Feedback Loop
```

---

## 60-second quick start

```bash
# 1. Configure
cp .env.example .env

# 2. (Optional) boot the full pipeline — Postgres / Redis / Meili / worker / API
docker compose up -d

# 3. Open the dashboard
#   Production:        https://<your>.vercel.app/
#   Local (Docker):    http://localhost:3000
#   Local (file://):   double-click apps/dashboard/index.html
```

The dashboard works **standalone** — it has its article corpus inlined and supports rating + preferences export without any backend. The full stack adds: real-time pipeline updates, semantic search, feedback ingestion, and PDF generation.

---

## Repository layout (v3)

```
apps/dashboard/         CANONICAL single-file UI (VnEconomy-style editorial)
apps/api/               FastAPI: REST + WebSocket
content/                canonical markdown intelligence artifacts (HYBRID alias)
  ├── reports/          daily + weekly intelligence reports
  ├── wiki/             Research Wiki — concepts, entities, sources (alias for /wiki)
  └── _templates/       markdown templates
raw/                    IMMUTABLE internet archive
cleaned/                normalized intermediates
generated/              dashboard feed (index.json, search-index.json, graph.json, embeddings-ready.json)
feedback/               human preference intelligence (ratings.json, analytics/, datasets/, inbox/)
prompts/                modular prompt library (system/, extraction/, summarization/, scoring/, formatting/, evaluation/)
scripts/                Python entry points (clean.py, summarize.py, build_index.py, ...)
schemas/                JSON Schemas (raw / report / rating / semantic)
packages/               internal libraries (agents/, automation/, shared/)
infra/docker/           Dockerfiles for api / worker / watcher / pdf
docs/                   architecture, data-flow, api, deployment, ui-design docs
logs/                   runtime logs
legacy/                 archived retired systems (intelligence-platform/, nextjs-dashboard/, k8s/, ...)
outputs/                lint reports, audits, ad-hoc exports
```

See `ARCHITECTURE.md` for the one-page system architecture and `CLAUDE.md` for operational instructions.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Single-file HTML + vanilla JS | Per ADR-002 — simplicity first. No build step. |
| Backend | FastAPI + Uvicorn + Pydantic v2 | Async, type-first, WebSocket-native. |
| DB | Postgres 16 + pgvector | Relational + vector in one engine. |
| Search | Meilisearch | Sub-50ms hybrid search, Vietnamese tokenizer. |
| Queue | Redis 7 | Celery broker + WebSocket fanout. |
| Orchestration | LangGraph + Celery | Stateful AI workflows. |
| File watcher | watchdog | Real-time `raw/` ingest. |
| LLMs | Anthropic Claude (primary), OpenAI (fallback) | Vietnamese fluency, long context. |
| Embeddings | `text-embedding-3-large` | 3072-dim, multilingual. |
| PDF | Puppeteer (Node microservice) | Pixel-perfect institutional reports. |
| Deploy (prod) | Vercel (static dashboard) + Render (API) | One-click, no infra ops. |
| Deploy (dev) | Docker Compose | Single-command local stack. |

**Forbidden** (ADR-010): Kubernetes, service mesh, microservices fragmentation, CQRS, premature scaling.

---

## Workflows

### Process today's clippings

```bash
python scripts/clean.py
python scripts/summarize.py --date 2026-05-18
python scripts/build_index.py
python scripts/build_graph.py
# Reload the dashboard.
```

### Process feedback

```bash
# Drop dashboard-exported preferences-YYYY-MM-DD.json into feedback/inbox/
python scripts/analyze_feedback.py
# Now inspect feedback/analytics/per-prompt-version.json — which prompt versions are winning?
```

### Run the live pipeline (Celery)

```bash
docker compose up -d        # postgres + redis + meili + minio + api + worker + beat + watcher + pdf + dashboard
# Drop a new markdown file into raw/news/YYYY-MM-DD/ — see it appear on the dashboard within seconds.
```

---

## Documents to read next

1. `ARCHITECTURE.md` — one-page system architecture
2. `CLAUDE.md` — operational instructions for AI agents working in this repo
3. `AGENTS.md` — vault content rules (immutability, naming, schemas)
4. `outputs/architecture-decisions-2026-05-18.md` — ADR-001 … ADR-011 (the full restructure rationale)
5. `outputs/audit-2026-05-18.md` — Phase 1 audit with fork resolutions
6. `MIGRATION.md` — what moved where during the v3 restructure
7. `schemas/report.schema.json` — the semantic surface every report carries
8. `docs/` — deeper docs on architecture, data flow, API, UI design system

---

## System invariants

- `raw/` is **immutable**. Agents never write here.
- Markdown is canonical; DB and `generated/*.json` are derived.
- Every report carries source attribution back to `raw/`.
- Every report carries `prompt_version` + `model` + `template_version` so feedback is traceable.
- `legacy/` is read-only — retired systems live there for recovery, not iteration.
- One canonical dashboard. One canonical API. One canonical pipeline. One canonical deploy path per environment.

---

## v3 restructure (2026-05-18)

This repository underwent an autonomous architecture reset on 2026-05-18 to eliminate duplicate systems (a parallel `intelligence-platform/` monorepo, a retired Next.js dashboard at `apps/web/`, Kubernetes infrastructure, multiple deploy targets). The retired systems are preserved in `legacy/` per ADR-011. See `MIGRATION.md` for the full move list and `scripts/cleanup-legacy.ps1` for the physical-move script.
