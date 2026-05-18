# Intelligence Platform — System Architecture

> Institutional-grade AI intelligence operating system built on top of an Obsidian vault.
> Source-of-truth design document. All implementation deviations must be reflected here.

---

## 0. Design principles

1. **Raw is immutable.** Anything in `/raw` is a frozen artifact. Processing reads, never writes.
2. **Wiki is AI-owned.** Concept and entity pages are generated and reconciled by agents.
3. **Every fact is traceable.** Each summary sentence carries a citation pointer back to its source span.
4. **Event-driven by default.** Files dropped into `/raw/news` produce events; everything downstream is a reaction.
5. **Idempotent re-runs.** Re-running classification or report generation on the same `news_item_id` produces the same output (modulo model drift, which we version).
6. **Observability before optimization.** Every agent invocation logs `(input_hash, model, prompt_version, latency_ms, cost_usd, output_hash)`.

---

## 1. System architecture (high-level)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            OBSIDIAN VAULT (filesystem)                       │
│   raw/  ───────  wiki/  ───────  Processed/  ───────  AGENTS.md             │
└──────────────────────────────────────────────────────────────────────────────┘
            │ (file events via Obsidian Web Clipper / Edge)
            ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│   INGESTION SERVICE  (Python, watchdog)                                      │
│   • detects new files in raw/news, raw/PDF Files, raw/Social Media Post      │
│   • computes content hash → de-dupe                                          │
│   • POST /v1/ingest to API                                                   │
└──────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│   FASTAPI BACKEND  (apps/api)                                                │
│   • persists raw record in Postgres                                          │
│   • emits "news.ingested" event to Redis stream                              │
│   • exposes REST + WebSocket to dashboard                                    │
└──────────────────────────────────────────────────────────────────────────────┘
            │ (webhook to n8n)              │ (WebSocket)
            ▼                                ▼
┌──────────────────────────────┐    ┌─────────────────────────────────────────┐
│   n8n  (visual orchestrator) │    │   NEXT.JS DASHBOARD  (apps/dashboard)   │
│   • ingest pipeline workflow │    │   • daily-news view                     │
│   • daily-report workflow    │    │   • report center                       │
│   • calls LangGraph over HTTP│    │   • semantic search                     │
└──────────────────────────────┘    │   • knowledge graph                     │
            │                        │   • PDF viewer + trace-back            │
            ▼                        └─────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────────────┐
│   LANGGRAPH AGENTS  (services/agents)  — single state machine, 7 nodes       │
│   ingest → classify → summarize → wiki_enrich → report → pdf → sync          │
└──────────────────────────────────────────────────────────────────────────────┘
            │              │              │
            ▼              ▼              ▼
┌─────────────────┐  ┌───────────────┐  ┌──────────────────────────────────┐
│  SUPABASE PG    │  │  MEILISEARCH  │  │  PDF ENGINE (Node + Puppeteer)   │
│  + pgvector     │  │  (semantic +  │  │  • renders React-PDF template    │
│  + RLS          │  │   lexical)    │  │  • signs URL, stores in Supabase │
└─────────────────┘  └───────────────┘  └──────────────────────────────────┘
```

---

## 2. Folder restructuring (vault)

The existing vault stays, but we formalize it:

```
/vault
├── raw/                                  # IMMUTABLE
│   ├── news/                             # web-clipped articles (md)
│   ├── pdf-files/                        # uploaded PDFs (renamed kebab-case)
│   ├── social-media-post/
│   └── old news/
│       └── YYYY-MM-DD/                   # archived after processing
│
├── wiki/                                 # AI-owned, agent-writable
│   ├── companies/
│   │   ├── vn/                           # Vietnamese corporates
│   │   └── intl/
│   ├── industries/                       # auto-created folders
│   │   ├── real-estate.md
│   │   ├── energy.md
│   │   └── ...
│   ├── macro/
│   │   ├── vn/
│   │   └── intl/
│   ├── concepts/                         # cross-cutting concepts
│   ├── sources/                          # per-source summary pages
│   ├── index.md                          # master catalog (agent-maintained)
│   └── log.md                            # append-only operation log
│
├── Processed/                            # canonical report outputs
│   ├── news/YYYY-MM-DD/
│   ├── social-media/YYYY-MM-DD/
│   ├── pdf-files/YYYY-MM-DD/
│   └── master/YYYY-MM-DD.md              # MASTER daily brief
│
└── AGENTS.md                             # agent operational memory + schemas
```

**Filename convention** (every artifact): `YYYY-MM-DD__source-slug__title-slug.md`.

---

## 3. Repository structure (monorepo)

```
intelligence-platform/
├── apps/
│   ├── dashboard/              # Next.js 15 App Router
│   └── api/                    # FastAPI
├── services/
│   ├── agents/                 # LangGraph
│   ├── ingestion/              # vault watcher
│   ├── workers/                # Celery
│   └── pdf-engine/             # Node + Puppeteer
├── packages/
│   ├── shared-types/           # TS types (generated from OpenAPI)
│   └── design-tokens/          # Tailwind preset
├── n8n/workflows/              # exported workflow JSON
├── infra/
│   ├── supabase/migrations/    # SQL
│   ├── railway/                # railway.toml per service
│   ├── vercel/                 # vercel.json
│   └── docker/                 # docker-compose.yml (local)
├── obsidian/plugin/            # companion plugin
└── docs/                       # ARCHITECTURE, DEPLOYMENT, ROADMAP
```

---

## 4. Database schema (Supabase Postgres + pgvector)

Eight core tables, all with `id uuid primary key default gen_random_uuid()`, `created_at`, `updated_at`.

### 4.1 Core entities

| Table | Purpose | Key columns |
|---|---|---|
| `news_items` | Immutable raw record per ingested file | `content_hash` (unique), `source_url`, `vault_path`, `publish_date`, `language`, `raw_text`, `status` (enum) |
| `summaries` | Structured AI summary | `news_item_id` (fk), `thesis`, `supporting_points` (jsonb[]), `implications` (jsonb[]), `model`, `prompt_version` |
| `classifications` | Multi-label assignment | `news_item_id`, `bucket` (enum: vn_corp/intl_corp/vn_macro/intl_macro), `industries` (text[]), `countries` (text[]), `companies` (text[]), `confidence` (float) |
| `reports` | Generated daily reports | `date`, `type` (enum: news/social/pdf/master), `body_md`, `pdf_url`, `version`, `prev_version_id` |
| `wiki_pages` | Agent-maintained concept/entity pages | `slug`, `type` (enum: concept/entity/source-summary/comparison), `body_md`, `frontmatter` (jsonb), `vault_path` |
| `entities` | Companies / industries / countries / people | `name`, `type`, `aliases` (text[]), `ticker`, `country`, `industry` |
| `embeddings` | Vector store | `owner_table`, `owner_id`, `chunk_index`, `content`, `vector vector(1536)` |
| `processing_jobs` | Pipeline state | `news_item_id`, `step` (enum), `status`, `attempts`, `last_error`, `started_at`, `finished_at` |

### 4.2 Linking tables

- `news_item_entities (news_item_id, entity_id, relevance float)`
- `wiki_page_sources (wiki_page_id, news_item_id, citation_text)` — every wiki claim is sourced
- `report_news_items (report_id, news_item_id, ordinal int)`

### 4.3 Indexes

```sql
-- de-dupe
create unique index on news_items (content_hash);

-- timeline
create index on news_items (publish_date desc);
create index on reports (date desc, type);

-- pgvector (HNSW for low-latency ANN)
create index on embeddings using hnsw (vector vector_cosine_ops);

-- trigram for fuzzy entity match
create extension if not exists pg_trgm;
create index on entities using gin (name gin_trgm_ops);
create index on entities using gin (aliases);

-- jsonb gin for classification filters
create index on classifications using gin (industries);
create index on classifications using gin (countries);
```

### 4.4 RLS posture

- All tables have RLS enabled.
- `service_role` bypasses (used by api/agents/workers).
- `authenticated` users can `select` everything (read-only intelligence consumers).
- No `anon` access. Future: per-workspace tenancy via `workspace_id`.

Full SQL: `infra/supabase/migrations/`.

---

## 5. Backend API design

FastAPI, versioned `/v1`. OpenAPI auto-generated → TS types in `packages/shared-types`.

### 5.1 Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v1/ingest` | Watcher → API. Creates `news_item`, enqueues pipeline. |
| `GET` | `/v1/news` | List with filters (`?bucket=vn_corp&industry=energy&date_from=…`). Paginated. |
| `GET` | `/v1/news/{id}` | Detail + classification + summary + linked entities. |
| `GET` | `/v1/news/{id}/trace` | Trace-back payload: source URL, vault path, report URLs, related wiki. |
| `GET` | `/v1/reports` | List reports (`?date=…&type=master`). |
| `GET` | `/v1/reports/{id}` | Single report body + PDF URL. |
| `POST` | `/v1/reports/{date}/regenerate` | Manual re-run for a given day. |
| `GET` | `/v1/reports/{id}/pdf` | 302 → signed Supabase storage URL. |
| `POST` | `/v1/search` | Semantic + lexical hybrid. Body: `{q, filters, k}`. |
| `GET` | `/v1/graph` | Knowledge graph slice (`?entity=VinGroup&depth=2`). |
| `POST` | `/v1/refresh` | Manual sync trigger (rescan vault, re-emit ingest events). |
| `GET` | `/v1/dashboard/today` | Aggregated daily view payload (single round-trip). |
| `POST` | `/v1/webhooks/n8n` | n8n → API callbacks (job completion). |
| `WS` | `/ws` | Server pushes `news.ingested`, `report.ready`, `pdf.ready`, `wiki.updated`. |

### 5.2 Request/response examples

**`POST /v1/ingest`**
```json
{
  "vault_path": "raw/news/2026-05-15__vneconomy__vingroup-q1-earnings.md",
  "content_hash": "sha256:…",
  "source_url": "https://vneconomy.vn/...",
  "title": "Vingroup Q1 2026 earnings beat",
  "publish_date": "2026-05-15",
  "raw_text": "…full markdown body…",
  "language": "vi"
}
→ 202 Accepted
{ "id": "8c…", "status": "queued", "pipeline_run_id": "pr_…" }
```

**`GET /v1/dashboard/today`**
```json
{
  "date": "2026-05-15",
  "headline": { "news_item_id": "…", "title": "…", "thesis": "…" },
  "buckets": {
    "vn_corp": { "count": 14, "by_industry": { "real-estate": 5, "banking": 4, … } },
    "intl_corp": { "count": 8, … },
    "vn_macro": { "count": 3, … },
    "intl_macro": { "count": 6, … }
  },
  "master_report": { "id": "…", "pdf_url": "…" },
  "recent_items": [ /* top 20, lazy-loaded */ ]
}
```

### 5.3 WebSocket protocol

Server → client only. Channel-based subscription via query param: `/ws?channels=news,reports`.

```ts
type WsEvent =
  | { type: "news.ingested"; data: NewsItem }
  | { type: "news.classified"; data: { id: string; bucket: Bucket; industries: string[] } }
  | { type: "report.ready"; data: { id: string; date: string; type: ReportType } }
  | { type: "pdf.ready"; data: { report_id: string; url: string } }
  | { type: "wiki.updated"; data: { slug: string } }
  | { type: "job.failed"; data: { news_item_id: string; step: string; error: string } };
```

---

## 6. AI agent architecture (LangGraph)

Single LangGraph state machine, seven nodes. State is persisted to Redis (checkpointer) so runs survive worker restarts. Each node is an `async` function returning a partial state.

```python
class PipelineState(TypedDict):
    news_item_id: str
    raw_text: str
    language: Literal["vi", "en"]
    classification: Optional[Classification]
    summary: Optional[StructuredSummary]
    entities: list[Entity]
    wiki_updates: list[WikiUpdate]
    report_inclusion: Optional[ReportInclusion]
    pdf_url: Optional[str]
    errors: list[str]

graph = StateGraph(PipelineState)
graph.add_node("ingestion",       ingestion_agent)
graph.add_node("classification",  classification_agent)
graph.add_node("summarization",   summarization_agent)
graph.add_node("wiki_enrichment", wiki_enrichment_agent)
graph.add_node("report",          report_generation_agent)
graph.add_node("pdf",             pdf_generation_agent)
graph.add_node("sync",            dashboard_sync_agent)

graph.set_entry_point("ingestion")
graph.add_edge("ingestion",       "classification")
graph.add_edge("classification",  "summarization")
graph.add_edge("summarization",   "wiki_enrichment")
graph.add_conditional_edges("wiki_enrichment", route_to_report)  # batch by day
graph.add_edge("report",          "pdf")
graph.add_edge("pdf",             "sync")
graph.add_edge("sync",            END)
```

### 6.1 Per-agent responsibilities

| Agent | Inputs | Outputs | Model | Notes |
|---|---|---|---|---|
| **Ingestion** | raw md + frontmatter | normalized `NewsItem` row, content hash | none (deterministic) | parses Obsidian Web Clipper YAML, detects language |
| **Classification** | normalized text | bucket + industries[] + countries[] + companies[] | Haiku 4.5 | structured output via function calling |
| **Summarization** | text + classification | `thesis` + `supporting_points[]` + `implications[]` + per-claim citation offsets | Sonnet 4.6 | enforces "first sentence = thesis" rule |
| **Wiki Enrichment** | summary + entities | upserts to `wiki_pages` (companies, industries, concepts) | Sonnet 4.6 | uses retrieval over existing wiki to merge, not duplicate |
| **Report Generation** | day's items + classifications + summaries | `Report` row (news/social/pdf/master) | Opus 4.6 | one Opus call per report type per day, batched |
| **PDF Generation** | report markdown | calls PDF engine, stores URL | none | Node service, not LLM |
| **Dashboard Sync** | all of the above | emits WS events, invalidates caches | none | last node, fast |

### 6.2 Prompt versioning

Prompts live under `services/agents/prompts/{agent}/v{N}.md`. The active version is pinned per agent in `agents/prompts/registry.py`. Every output stores the prompt version → reproducibility.

### 6.3 Retrieval (RAG)

Wiki enrichment and report generation both retrieve over the embeddings table:
1. Embed query (last 7 days of headlines + the new item's entities).
2. `vector_cosine_ops` HNSW search, top-K=20.
3. Re-rank with cross-encoder (optional, behind a feature flag).
4. Inject into prompt with `[wiki:{slug}]` markers; outputs maintain those markers so we can resolve back to wiki sources.

---

## 7. Automation pipeline (n8n + Celery)

Two layers:

**Layer A — n8n (visual workflows)** owns the *business* pipeline. Three workflows:

1. **`ingest-news`** — triggered by webhook from API.
   `Webhook → HTTP node (call agents/run) → IF (success) → HTTP (mark done) ELSE → wait+retry → DLQ`
2. **`daily-report`** — cron at 06:00 Asia/Ho_Chi_Minh.
   `Cron → HTTP (agents/build-report?type=master) → HTTP (pdf-engine/render) → HTTP (api/notify)`
3. **`weekly-wiki-lint`** — cron Sunday 22:00.
   `Cron → HTTP (agents/wiki-lint) → write outputs/lint-YYYY-MM-DD.md`

**Layer B — Celery (queue workers)** owns *technical* work n8n shouldn't touch: long-running embedding batches, retry storms, deduplication.

Queues: `ingest`, `classify`, `report`, `pdf`, `sync`. Each has its own worker pool size.

Retry policy: exponential backoff `(2^n) seconds, max 5 attempts, dead-letter to processing_jobs.status='dlq'`. Dashboard surfaces DLQ count as an SLO.

---

## 8. Obsidian integration strategy

Three integration points, in order of robustness:

1. **Filesystem watcher** (primary). `services/ingestion` runs `watchdog` against `/vault/raw/news`. Filesystem events are debounced (250ms) and de-duplicated by content hash before hitting the API. Works regardless of how files arrive — Web Clipper, manual copy, sync clients.

2. **Companion Obsidian plugin** (`obsidian/plugin`). Optional but recommended. Adds:
   - "Send to Intelligence" command (sends current note immediately, bypassing the 250ms debounce).
   - Inline status badge under the note title: *queued / classified / reported*.
   - Command palette: "Open generated report" → opens `Processed/...` for the current note.

3. **Webhook from external clipper** (`POST /v1/ingest`). For arbitrary clients (Edge extension, mobile share sheet).

**Move-to-archive logic.** After `sync` agent completes, the watcher renames the source file from `raw/news/X.md` → `raw/old news/YYYY-MM-DD/X.md` *atomically* (rename within same volume = atomic). This satisfies the immutability rule: the file is preserved bit-for-bit, only its path changes.

**Wiki write-back.** Agents write wiki pages to Postgres first; a separate `wiki_writeback_worker` (Celery, runs every 60s) reconciles changed wiki rows into `/vault/wiki/*.md` files so Obsidian sees them. Conflict policy: DB wins on schema fields (frontmatter), filesystem wins on free-form body if `manual_edit=true` flag set in frontmatter.

---

## 9. Dashboard system design

Next.js 15 App Router, Server Components for data fetching, Client Components for interactivity. Realtime via native WebSocket + Supabase Realtime as fallback.

### 9.1 Routes

```
/                                   Daily intelligence view (default)
/daily/[date]                       Specific day
/reports                            Report center (list)
/reports/[id]                       Report viewer + PDF preview
/search                             Semantic search
/graph                              Knowledge graph
/wiki/[slug]                        Wiki page browser
/settings                           Filters, theme, connections
```

### 9.2 Component hierarchy

```
<AppShell>
├── <Sidebar />                     (route nav, filter pinning, refresh)
├── <TopBar>
│   ├── <DateScrubber />
│   ├── <GlobalSearch />            (Cmd-K)
│   └── <RefreshButton />           (calls POST /v1/refresh)
└── <main>
    ├── <DailyHeadline />           (biggest item, thesis sentence)
    ├── <BucketGrid>
    │   ├── <BucketCard bucket="vn_corp">
    │   │   └── <IndustryAccordion> (auto-grouped)
    │   ├── <BucketCard bucket="intl_corp" />
    │   ├── <BucketCard bucket="vn_macro" />
    │   └── <BucketCard bucket="intl_macro" />
    ├── <NewsItemDetail />          (slide-over panel, trace-back, related wiki)
    └── <FilterDock />              (industry, country, company, theme)
```

### 9.3 State management

- **Server state**: React Query (TanStack Query) keyed by `/v1/...` URLs. SSR hydration from Server Components.
- **Filter state**: URL search params (sharable + bookmark-friendly). `useFilters()` hook syncs to/from URL.
- **WS events**: zustand store `useLiveStore`, invalidates React Query keys on `news.ingested` / `report.ready` events.
- **No global app state** beyond filters and WS.

### 9.4 Design system

Inspired by soulslab.co. Tokens in `packages/design-tokens/tailwind.preset.ts`:

| Token | Value | Purpose |
|---|---|---|
| `bg.canvas` | `#0a0b0e` | Page background |
| `bg.glass` | `rgba(255,255,255,0.04)` + `backdrop-blur-xl` | Card surface |
| `bg.glass-hover` | `rgba(255,255,255,0.07)` | Hover state |
| `border.subtle` | `rgba(255,255,255,0.08)` | Card edges |
| `text.primary` | `#f5f5f7` | Body text |
| `text.muted` | `#9aa0a6` | Captions |
| `accent.gold` | `#c9a86a` | Numbers, dates, key metrics |
| `accent.signal` | `#7eb6ff` | Links, interactive |
| `signal.bullish` | `#56d364` | Positive sentiment |
| `signal.bearish` | `#f85149` | Negative |
| `gradient.aurora` | `linear-gradient(135deg, #0a0b0e, #1a1b2e, #0a0b0e)` | Hero backgrounds |

Type: Inter Variable for body, JetBrains Mono for numbers, Fraunces for editorial headers.

Motion: Framer Motion. `easeInOut, 0.45s` for page transitions; `spring, stiffness=180, damping=22` for cards. No bounces on data updates — that's how you make a dashboard look unprofessional.

### 9.5 Filtering system

URL-driven, multi-select chips at the top of the daily view:

```
/daily/2026-05-15?bucket=vn_corp&industry=energy,real-estate&country=vn
```

The `<FilterDock />` reads from `useFilters()`, surfaces active chips, supports save-as-preset (stored in Supabase per user).

### 9.6 Trace-back UX

Click any news item → slide-over panel with four anchored buttons:
1. **Open source** (original URL, new tab)
2. **Open in vault** (deep link to Obsidian: `obsidian://open?vault=...&file=raw%2Fnews%2F...`)
3. **Open report** (jumps to `/reports/{id}` with the item highlighted)
4. **Related wiki** (lateral list of `wiki_pages` joined via `news_item_entities`)

---

## 10. PDF engine

Node service, `services/pdf-engine`. Two rendering paths, switched per template:

1. **React-PDF** (`@react-pdf/renderer`) for structured reports — better typography control, deterministic output, no headless browser.
2. **Puppeteer** for any HTML template that needs full CSS/charts — falls back here when a report includes Recharts visualizations.

Endpoints:
- `POST /render` body: `{template, data, options}` → returns `{pdfBytes}` (base64) or `{url}` (uploaded to Supabase Storage).
- `GET /healthz`

Templates (`services/pdf-engine/templates/`):
- `daily-brief.tsx` — single-day, one bucket
- `master-report.tsx` — full daily MASTER report (cover, exec summary, sections, sources)
- `weekly-digest.tsx` — Sunday roll-up

Output naming: `Processed/master/YYYY-MM-DD.pdf` and `news_items[].pdf_url` points to signed Supabase Storage URLs.

---

## 11. Automation flow — concrete walkthrough

A user clips a Vietnamese real-estate article into `/raw/news/`. T = 0.

| t (s) | Service | Action |
|---|---|---|
| 0.0 | Obsidian Web Clipper | writes md to `raw/news/2026-05-15__cafef__novaland-debt-restructure.md` |
| 0.25 | `services/ingestion` | watchdog fires `on_created`, debounce window opens |
| 0.50 | `services/ingestion` | parses frontmatter, computes sha256, POST /v1/ingest |
| 0.55 | `apps/api` | inserts `news_items` row (status=queued), emits webhook to n8n |
| 0.60 | n8n | `ingest-news` workflow starts, HTTPs `agents/run` |
| 0.6→3 | `services/agents` (LangGraph) | classification → bucket=vn_corp, industries=[real-estate] |
| 3→7 | | summarization → thesis + 4 supporting points + 3 implications |
| 7→9 | | wiki_enrichment → updates `wiki/companies/vn/novaland.md`, `wiki/industries/real-estate.md` |
| 9 | | (batched) report agent waits for daily window or threshold |
| 9.1 | `apps/api` | WS event `news.classified` → dashboard updates live count |
| 9.2 | `services/ingestion` | atomic rename to `raw/old news/2026-05-15/...` |
| ~06:00 next day | n8n | `daily-report` cron fires |
| | `services/agents` | builds master report from yesterday's items |
| | `services/pdf-engine` | renders master-report.tsx → PDF, stores in Supabase Storage |
| | `apps/api` | WS event `report.ready` + `pdf.ready` |

---

## 12. Security model

- Auth: Supabase Auth (JWT). API validates JWT signature against `SUPABASE_JWT_SECRET`.
- Service-to-service: signed HMAC headers on internal webhooks (api ↔ n8n ↔ agents).
- Secrets: Railway secret manager + Vercel env. Never in repo.
- Vault writes: only `wiki_writeback_worker` has write access to `/vault/wiki`. API/agents write to DB only.
- RLS on every table. `service_role` keys only inside backend services, never shipped to the frontend.
- PDF URLs are short-lived signed URLs (15 min TTL).
- Rate limiting: 60 req/min/user on `/v1/search`, 10/min on `/v1/refresh`.
- Audit trail: `audit_log` table captures every `INSERT/UPDATE/DELETE` on `wiki_pages` and `reports` via Postgres triggers.

---

## 13. Scalability strategy

**Phase 0–2 (1 user, <500 articles/day):** single Railway service per role, free-tier Supabase. ~$30/mo.

**Phase 3 (10 users, <5k articles/day):**
- Promote Supabase to Pro ($25/mo, read replicas + larger compute).
- Split Celery into per-queue workers (ingest gets 4 workers, others 2).
- Add Meilisearch Cloud or self-host on a dedicated Railway service.
- Cache `GET /v1/dashboard/today` for 30s.

**Phase 4 (50+ users, 50k articles/day):**
- Move embeddings to a dedicated read replica (vector queries are heavy).
- Hot/cold split: items older than 90 days move to a `news_items_archive` partition.
- Front the API with Cloudflare for static cache + DDoS.
- Promote n8n to self-hosted (queue mode) on a dedicated VM.
- GPU box for local embedding model (cuts OpenAI embedding cost ~90%).

**Bottlenecks, in expected order:**
1. **Anthropic/OpenAI rate limits** — solve by batching summaries (5 items per call) and using Haiku for classification.
2. **pgvector index size** — solve by partitioning `embeddings` by month, vacuuming aggressively.
3. **Frontend cold start** — solve via Vercel ISR for `/daily/[date]` pages.
4. **Watcher single-point-of-failure** — solve by running 2 watchers with file lock (Redis SETNX).

---

## 14. Event-driven architecture

Every state transition emits an event to a Redis stream. Two streams:

- `events.news` — fine-grained: `news.ingested`, `news.classified`, `news.summarized`, `news.wiki_enriched`.
- `events.reports` — `report.requested`, `report.built`, `pdf.rendered`, `report.published`.

Consumers (Celery workers, WebSocket fan-out, audit logger) subscribe via consumer groups so we can add new consumers without touching publishers. Events are JSON, schema-versioned: `{v: 1, type, ts, payload}`.

---

## 15. Deployment architecture

```
┌─ vercel.com ─────────────────────────────────┐
│  apps/dashboard  (Edge + ISR + RSC)         │
└──────────────────────────────────────────────┘
              │  (HTTPS, CORS allowed origin)
              ▼
┌─ railway.app ────────────────────────────────┐
│  ┌──────────────┐ ┌──────────────┐          │
│  │   api        │ │   agents     │  HTTP    │
│  │  FastAPI     │ │  LangGraph   │  ←──→    │
│  └──────────────┘ └──────────────┘          │
│  ┌──────────────┐ ┌──────────────┐          │
│  │   workers    │ │  pdf-engine  │          │
│  │   Celery     │ │  Puppeteer   │          │
│  └──────────────┘ └──────────────┘          │
│  ┌──────────────┐ ┌──────────────┐          │
│  │   watcher    │ │     n8n      │          │
│  │  (sidecar)   │ │  (self-host) │          │
│  └──────────────┘ └──────────────┘          │
│              Upstash Redis (broker)         │
└──────────────────────────────────────────────┘
              │
              ▼
┌─ supabase.com ───────────────────────────────┐
│  Postgres 16 + pgvector + RLS + Storage      │
│  Auth (JWT)                                  │
└──────────────────────────────────────────────┘
```

CI/CD: GitHub Actions
- On push to `main`: build all services, run typecheck + tests, deploy via Railway CLI (api/agents/workers/pdf-engine), Vercel auto-deploys dashboard, Supabase migrations applied via `supabase db push` in a manual approval step.

---

## 16. Implementation roadmap

### Phase 0 — Foundations (Week 1)
- Repo scaffolded (this commit)
- Supabase project, schema migration applied
- Watcher → API → DB round-trip working
- **Acceptance:** drop a markdown file in `raw/news`, see a `news_items` row appear within 5s.

### Phase 1 — MVP (Week 2–3)
- LangGraph classify + summarize agents
- Daily master report generation (Markdown only, no PDF yet)
- **Acceptance:** at 06:00, `Processed/master/YYYY-MM-DD.md` exists and reads like a brief.

### Phase 2 — Dashboard (Week 4–5)
- Next.js dashboard live on Vercel
- Daily view + filters + trace-back panel + WebSocket live counts
- **Acceptance:** new ingest visibly increments the count without a page refresh.

### Phase 3 — PDF + Search (Week 6–7)
- PDF engine wired up; master report exports
- Meilisearch indexing + hybrid search
- **Acceptance:** sub-200ms search across 30 days of items.

### Phase 4 — Wiki + Graph (Week 8–9)
- Wiki enrichment agent
- Knowledge graph view
- Wiki write-back to Obsidian
- **Acceptance:** clicking a company name shows a populated wiki page + graph slice.

### Phase 5 — Scale (Month 3+)
- Read replicas, partitioning, caching, alerting (Sentry + Grafana Cloud)
- Multi-user RLS hardening
- **Acceptance:** p95 dashboard load <800ms at 10k items/day.

---

## 17. Tech stack — final recommendation

| Layer | Pick | Why |
|---|---|---|
| Frontend | **Next.js 15 + Tailwind + shadcn/ui + Framer Motion** | Spec-mandated, also the right call. RSC for the daily view = fastest possible TTFB. |
| API | **FastAPI** | Async-native, OpenAPI-first, ideal for AI-heavy backends. |
| ORM | **SQLAlchemy 2 (async) + Alembic** | Mature; pairs cleanly with FastAPI. |
| Orchestration | **n8n + LangGraph** | n8n for human-editable workflows; LangGraph for typed agent state. |
| Queue | **Celery + Redis** | Boring, reliable, well-understood. |
| DB | **Supabase Postgres + pgvector** | One vendor for SQL + auth + storage + realtime. |
| Search | **Meilisearch** | Faster setup than Elasticsearch; sufficient at this scale. |
| Embeddings | **OpenAI `text-embedding-3-large`** | Best quality/$ at MVP; swap for `BGE-M3` on a GPU when scaling. |
| LLM | **Claude (Opus/Sonnet/Haiku tiered)** | Haiku for cheap classification, Sonnet for summaries, Opus for daily reports. |
| PDF | **React-PDF (primary) + Puppeteer (fallback)** | Determinism + chart support. |
| Realtime | **Native WebSocket from FastAPI** | One protocol; no Supabase Realtime quota burn. |
| Auth | **Supabase Auth (JWT)** | Single tenant for now; trivial to migrate to Clerk later. |
| Hosting | **Vercel + Railway + Supabase + Upstash** | Zero ops; ~$30/mo at MVP. |
| Observability | **Sentry (errors) + OpenTelemetry → Grafana Cloud** | Free tiers cover MVP. |

---

## 18. Tradeoffs we explicitly accepted

- **n8n over Temporal:** Lost durable workflow semantics (Temporal would survive worker crashes mid-step). Won visual editability for the non-engineer operator. Migration path: wrap critical n8n HTTP calls in idempotent Celery tasks; if we outgrow this, move just the daily-report pipeline to Temporal.
- **Supabase over self-hosted Postgres:** Lost some control over `pgvector` extension version. Won auth, storage, realtime, dashboard for free. We'll migrate to Neon + Clerk if Supabase pricing becomes a problem.
- **Polling watcher over inotify-only:** Watcher does a periodic full scan every 5 min as a safety net. Costs CPU; catches files that arrived during a watchdog crash.
- **Monorepo over polyrepo:** Lost CI parallelism granularity. Won shared types and atomic cross-service refactors. Turbo's caching covers most of the lost parallelism.

---

## 19. What's intentionally NOT in v1

- Authentication beyond single-user (RLS scaffolded but unused)
- Multi-language UI (Vietnamese-first content, English UI)
- Mobile-native app (responsive web is enough)
- On-device LLM
- Knowledge graph editing (read-only in v1)
- Alerts / digests via email or Slack (queued for Phase 4)

---

## 20. First MVP — concrete definition

**You can demo the MVP when:**
1. A new file in `raw/news` produces a `news_items` row within 5 seconds.
2. Within 60 seconds, the row has a `classification` and a `summary` filled in.
3. The dashboard at `/` shows the new headline live without refresh.
4. At 06:00 the next day, `Processed/master/YYYY-MM-DD.md` exists.
5. The trace-back panel for any news item opens its source URL, vault file, and report.

**That's it.** Everything beyond this is Phase 2+.
