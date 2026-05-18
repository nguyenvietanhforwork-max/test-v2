# Atlas — Full System Architecture

> Read this after `ARCHITECTURE.md`. This file dives deep.

## 1. Service topology

```
                       ┌─────────────────────┐
                       │  Cloudflare / nginx │
                       └──────────┬──────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                ▼                 ▼                 ▼
        ┌──────────────┐   ┌──────────────┐  ┌─────────────┐
        │  web (Next)  │   │  api (FastAPI)│  │ pdf (Node) │
        │   :3000      │   │    :8000      │  │   :4000    │
        └──────┬───────┘   └──┬─────────┬──┘  └──────┬─────┘
               │              │         │            │
               │  REST / WS   │ Redis   │ pg         │
               └──────────────┘ pub/sub │            │
                                        ▼            ▼
                              ┌────────────────────────────┐
                              │ postgres + pgvector :5432  │
                              │ redis :6379                │
                              │ meilisearch :7700          │
                              │ minio :9000 (PDF blobs)    │
                              └────────────────────────────┘
                                        ▲
                                        │
                              ┌─────────┴──────────┐
                              │  worker (Celery +  │
                              │  LangGraph)        │
                              │                    │
                              │  watcher (watchdog)│
                              └────────────────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │  raw/ wiki/        │
                              │  Processed/        │
                              │  (volume mount)    │
                              └────────────────────┘
```

## 2. Three planes

### Data plane

- **Postgres** is the source of truth for everything queryable (news items, entities, reports, embeddings).
- **Filesystem (vault)** is the source of truth for human-readable knowledge (markdown).
- **Meilisearch** is a derived index, rebuildable from Postgres at any time.
- **MinIO / S3** stores immutable PDF blobs; Postgres stores the metadata + URL.
- pgvector lives in the same Postgres instance to keep joins between text and vectors cheap.

### Control plane

- **Redis Streams** carry pipeline events: `ingest`, `enrich`, `report`, `publish`.
- **LangGraph** persists workflow state in Postgres (`langgraph_state` table).
- **Celery Beat** schedules: 06:00 ICT daily report; 07:00 Monday weekly synthesis; hourly reconcile.
- **Temporal** (optional, for long durable workflows) handles multi-day report cycles.

### Realtime plane

- Workers `PUBLISH` to Redis channel `events:<user_id>`.
- API subscribes per WebSocket connection.
- Frontend receives typed events: `news.created`, `report.published`, `pipeline.step`, `embedding.done`.

## 3. Repository structure (full)

```
apps/
├── web/                            # Next.js 14
│   ├── app/
│   │   ├── (dashboard)/            # Authed routes
│   │   │   ├── layout.tsx          # Shell: sidebar, command palette, WS provider
│   │   │   ├── page.tsx            # /  → daily intelligence
│   │   │   ├── reports/
│   │   │   │   ├── page.tsx        # /reports → archive
│   │   │   │   └── [id]/page.tsx   # /reports/:id → report + pdf
│   │   │   ├── graph/page.tsx      # /graph → knowledge graph
│   │   │   ├── search/page.tsx     # /search → semantic search
│   │   │   ├── industries/[slug]/  # /industries/banking
│   │   │   └── entities/[slug]/    # /entities/vingroup
│   │   ├── api/
│   │   │   └── auth/[...]/route.ts
│   │   ├── globals.css
│   │   └── layout.tsx              # Root layout + theme provider
│   ├── components/
│   │   ├── ui/                     # shadcn primitives
│   │   ├── dashboard/
│   │   │   ├── DailyBriefHeader.tsx
│   │   │   ├── IntelligenceFeed.tsx
│   │   │   ├── NewsCard.tsx
│   │   │   ├── ThesisPanel.tsx
│   │   │   ├── IndustryHeatmap.tsx
│   │   │   ├── EntityRail.tsx
│   │   │   └── PipelineStatusBar.tsx
│   │   ├── report/
│   │   │   ├── ReportViewer.tsx
│   │   │   ├── PdfPreview.tsx
│   │   │   └── SourceCitations.tsx
│   │   ├── graph/
│   │   │   └── KnowledgeGraph.tsx  # d3-force or cytoscape
│   │   ├── search/
│   │   │   └── CommandPalette.tsx  # cmd-k
│   │   └── motion/
│   │       └── CinemaTransition.tsx
│   ├── lib/
│   │   ├── api.ts                  # typed fetch client
│   │   ├── ws.ts                   # WebSocket client
│   │   ├── store.ts                # Zustand store
│   │   ├── format.ts               # date, number, currency
│   │   └── types.ts                # generated from OpenAPI
│   ├── styles/
│   │   ├── tokens.css              # design tokens (CSS vars)
│   │   └── motion.css              # keyframes, easings
│   ├── public/
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── next.config.js
│   └── package.json
│
└── api/                            # FastAPI
    ├── app/
    │   ├── main.py                 # ASGI entrypoint
    │   ├── core/
    │   │   ├── config.py           # pydantic-settings
    │   │   ├── security.py         # JWT, password hashing
    │   │   ├── logging.py          # structlog config
    │   │   └── deps.py             # FastAPI dependencies
    │   ├── db/
    │   │   ├── base.py             # SQLAlchemy Base
    │   │   ├── session.py
    │   │   └── models.py           # all SQLAlchemy models
    │   ├── schemas/                # Pydantic v2 schemas
    │   │   ├── news.py
    │   │   ├── report.py
    │   │   ├── entity.py
    │   │   └── search.py
    │   ├── api/v1/
    │   │   ├── router.py           # versioned router aggregator
    │   │   ├── news.py             # /news/*
    │   │   ├── reports.py          # /reports/*
    │   │   ├── entities.py         # /entities/*
    │   │   ├── industries.py       # /industries/*
    │   │   ├── search.py           # /search/*  (hybrid + semantic)
    │   │   ├── graph.py            # /graph/*
    │   │   ├── vault.py            # /vault/refresh, /vault/status
    │   │   └── ws.py               # WebSocket /ws/stream
    │   ├── services/               # business logic, framework-agnostic
    │   │   ├── ingest.py
    │   │   ├── report_builder.py
    │   │   ├── pdf_renderer.py
    │   │   ├── search.py
    │   │   ├── graph.py
    │   │   └── vault.py
    │   ├── events/                 # Redis pub/sub
    │   │   ├── bus.py
    │   │   └── types.py
    │   └── tasks/                  # Celery task defs (kept thin)
    │       └── jobs.py
    ├── alembic/
    │   ├── env.py
    │   └── versions/0001_init.py
    ├── tests/
    ├── pyproject.toml
    ├── alembic.ini
    └── Dockerfile

packages/
├── automation/                     # Python workers
│   ├── watcher/
│   │   ├── observer.py             # watchdog handler
│   │   └── reconcile.py            # periodic vault ↔ db diff
│   ├── pipeline/
│   │   ├── graph.py                # LangGraph state machine
│   │   ├── nodes/
│   │   │   ├── extract.py
│   │   │   ├── classify.py
│   │   │   ├── summarize.py
│   │   │   ├── embed.py
│   │   │   ├── persist.py
│   │   │   └── publish.py
│   │   └── state.py                # typed pipeline state
│   ├── reporting/
│   │   ├── daily_brief.py
│   │   ├── master_report.py
│   │   └── weekly_synthesis.py
│   ├── pdf/
│   │   └── client.py               # calls pdf microservice
│   └── pyproject.toml
│
├── agents/                         # LLM agents
│   ├── prompts/
│   │   ├── extractor.txt
│   │   ├── classifier.txt
│   │   ├── summarizer.txt
│   │   ├── thesis_generator.txt
│   │   └── industry_router.txt
│   ├── tools/                      # function-call tools available to agents
│   │   ├── search_wiki.py
│   │   ├── find_entity.py
│   │   ├── lookup_ticker.py
│   │   └── citation_check.py
│   ├── models/                     # provider abstraction
│   │   ├── base.py
│   │   ├── anthropic.py
│   │   └── openai.py
│   └── memory/
│       └── agents_md.py            # read/write AGENTS.md
│
└── shared/                         # cross-runtime types
    ├── schemas.json                # canonical JSON Schema
    ├── ts/                         # generated TS types
    └── py/                         # generated pydantic models

infra/
├── docker/
│   ├── web.Dockerfile
│   ├── api.Dockerfile
│   ├── worker.Dockerfile
│   ├── watcher.Dockerfile
│   └── pdf.Dockerfile
├── compose/
│   ├── docker-compose.yml          # dev
│   └── docker-compose.prod.yml
├── k8s/
│   ├── namespace.yaml
│   ├── api.deploy.yaml
│   ├── worker.deploy.yaml
│   ├── web.deploy.yaml
│   ├── postgres.statefulset.yaml
│   └── ingress.yaml
└── terraform/
    └── (cloud-specific)
```

## 4. Data flow (happy path)

```
1. User saves clipping with Obsidian Web Clipper
       ↓
2. File appears at raw/news/2026-05-15--reuters--vingroup-earnings.md
       ↓
3. watchdog observer fires `FileCreatedEvent`
       ↓
4. observer.py validates frontmatter, computes content hash, XADD to Redis Stream `ingest`
       ↓
5. Celery worker picks up event, hands to LangGraph
       ↓
6. LangGraph nodes (sequential):
      extract     → title, url, source, date, body
      classify    → bucket (VN/Intl × Macro/Corp) + industry + countries
      summarize   → thesis + 3-5 supporting points + implications
      embed       → 3072-d vector via OpenAI
      persist     → INSERT news_items, entities, embedding; UPSERT wiki note
      publish     → PUBLISH events:<user_id> {type:'news.created', ...}
       ↓
7. FastAPI WebSocket fanout pushes event to dashboard
       ↓
8. Dashboard inserts card with motion entry animation
       ↓
9. Daily 06:00 ICT job builds the morning brief (md + pdf)
```

## 5. Database schema (overview)

See [`docs/api.md`](./api.md) for endpoint shapes; see `apps/api/alembic/versions/0001_init.py` for the canonical schema. Tables:

- `news_items` — every clipping (1:1 with `raw/news/*.md`)
- `entities` — companies, tickers, people, places
- `entity_aliases` — alternate names (VIC ↔ Vingroup ↔ Tập đoàn Vingroup)
- `industries` — 28 sectors + auto-discovered
- `news_entities` — many-to-many w/ relevance score
- `news_industries` — many-to-many
- `embeddings` — pgvector(3072), foreign-key to news_items
- `reports` — daily, weekly, master, on-demand
- `report_sections` — structured sections inside a report
- `report_sources` — back-citation to news_items
- `pipeline_runs` — every LangGraph execution
- `pipeline_steps` — node-level traces (input/output token counts, latency)
- `pipeline_dead_letters` — failed runs awaiting human triage
- `wiki_pages` — index of `wiki/` markdown (path, frontmatter, hash)
- `users` — minimal: id, email, password_hash, role
- `audit_log` — all mutations to wiki/Processed

## 6. API surface (high-level)

```
GET    /api/v1/news?date=&industry=&entity=&q=     paginated feed
GET    /api/v1/news/:id                            single item + relations
POST   /api/v1/news/refresh                        manual vault sync trigger

GET    /api/v1/reports?type=daily&from=&to=
GET    /api/v1/reports/:id
GET    /api/v1/reports/:id/pdf                     stream pdf
POST   /api/v1/reports/build                       on-demand generation

GET    /api/v1/entities/:slug
GET    /api/v1/entities/:slug/timeline             news referencing entity
GET    /api/v1/industries
GET    /api/v1/industries/:slug/heatmap

POST   /api/v1/search                              { query, mode: 'lexical'|'semantic'|'hybrid' }
GET    /api/v1/graph?center=&depth=                knowledge graph slice

GET    /api/v1/vault/status                        files, drift, pipeline health
POST   /api/v1/vault/reconcile                     force full reconcile

WS     /ws/stream                                  realtime events
```

Full request/response shapes in [`docs/api.md`](./api.md).

## 7. Frontend architecture

- **App router** with one shell layout (`app/(dashboard)/layout.tsx`) containing sidebar, command palette, WS provider.
- **Server Components** for heavy reads (`/`, `/reports`, `/entities/:slug`).
- **Client Components** for everything interactive (cards, graphs, PDF viewer, palette).
- **State**: Zustand store keeps WS-pushed events; React Query handles fetch/cache.
- **Motion**: Framer Motion for entry animations, layout transitions, route fades.
- **Charts**: Recharts (line, bar) + d3 (graph, force layout).
- **PDF**: `<iframe src=…>` for server-rendered, `@react-pdf/renderer` for client preview.
- **i18n**: `next-intl` — Vietnamese + English.
- **Theming**: CSS vars in `tokens.css` driven by `data-theme` attribute (`dark`, `light`, `cinema`).

See [`docs/ui-design-system.md`](./ui-design-system.md) for tokens, motion language, and component contracts.

## 8. AI agent orchestration

LangGraph topology (DAG with conditional edges):

```
START → extract ──► classify ──► summarize ──► embed ──► persist ──► publish → END
              │            │                                     ▲
              │            └───[unknown industry]──► industry_router (auto-create folder)
              │
              └─[bad frontmatter]──► quarantine_node → END
```

Each node:
- pure function `(state) → state` over a `PipelineState` TypedDict
- LLM-bound nodes use the provider abstraction in `packages/agents/models/`
- prompts live in `packages/agents/prompts/*.txt` so they're versionable and testable
- `tools/` directory exposes function-callable utilities to the LLM (Anthropic tool use)

Retry policy per node:
- transient (HTTP 5xx, timeout): 3 attempts with exponential backoff
- semantic failure (LLM returns malformed JSON): re-prompt with the schema, max 2
- hard failure: write to `pipeline_dead_letters`, emit `pipeline.failed` event

## 9. Automation pipeline

| Trigger | Source | Action |
|---|---|---|
| File created in `raw/news/` | watchdog | Enqueue ingest event |
| File created in `raw/PDF Files/` | watchdog | Run PDF→md → ingest |
| Cron `0 23 * * *` (06:00 ICT) | Celery Beat | Build daily brief |
| Cron `0 0 * * 1` (07:00 ICT Mon) | Celery Beat | Build weekly synthesis |
| Cron `0 * * * *` | Celery Beat | Reconcile vault ↔ DB |
| Manual trigger | API `POST /vault/refresh` | Full re-scan |

## 10. Security model

- **Auth**: JWT (HS256, 1h access + 30d refresh). NextAuth.js or Lucia on the frontend.
- **mTLS** between worker and API for internal endpoints (`/internal/*`).
- **Vault FS**: `api` mounts vault read-only; `worker` is the only RW writer.
- **Secrets**: HashiCorp Vault or 1Password Connect in prod; `.env` only in dev.
- **PII redaction**: regex + LLM-based redactor for Vietnamese national ID, phone, email before sending payload to external LLMs.
- **Rate limit**: 60 req/min/user via Redis token bucket.

## 11. Observability

- **Logs**: structlog → JSON → Loki
- **Metrics**: Prometheus exporters on api/worker (request latency, queue depth, LLM token spend)
- **Traces**: OpenTelemetry — each pipeline run is a trace, each node a span
- **Alerts**: Grafana → Slack when DLQ > 5 or daily brief fails

## 12. Scalability strategy

| Layer | Scale-out approach |
|---|---|
| `web` | Stateless; horizontal pods behind ingress |
| `api` | Stateless; sticky WS by `user_id mod N` |
| `worker` | Celery concurrency; Redis Stream consumer groups |
| `postgres` | Primary + 2 read replicas; logical sharding by `created_at` quarter when >100M rows |
| `meilisearch` | Read replicas for search QPS |
| `pdf` | Multiple Puppeteer instances with content-hash dedupe cache |

## 13. Local dev workflow

```bash
# one-time
cp .env.example .env
docker compose up -d postgres redis meilisearch

# api
cd apps/api
uv sync
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# web
cd apps/web
pnpm install
pnpm dev

# worker
cd packages/automation
uv sync
celery -A worker worker --loglevel=info

# watcher
python -m packages.automation.watcher.observer
```
