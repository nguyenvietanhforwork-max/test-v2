# Atlas — System Architecture (one-pager)

```
┌────────────────────────── INGEST ────────────────────────────┐
│                                                              │
│   Obsidian Web Clipper (Edge)                                │
│              │                                               │
│              ▼                                               │
│        raw/news/*.md  ◀── immutable, human-curated           │
│              │                                               │
│              ▼ (fsevent)                                     │
│        watchdog observer  ────────► Redis Stream `ingest`    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────── PROCESSING (LangGraph) ───────────────────┐
│                                                              │
│   ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐    │
│   │ Extract │──▶│Classify │──▶│ Summarize│──▶│ Embed +  │    │
│   │  (LLM)  │   │ (LLM+   │   │ (LLM)    │   │ Persist  │    │
│   │         │   │ rules)  │   │          │   │ (pgvector│    │
│   └─────────┘   └─────────┘   └──────────┘   └──────────┘    │
│        │             │             │              │         │
│        ▼             ▼             ▼              ▼         │
│   entities      industries     thesis +       Postgres +    │
│   companies     countries      bullets        Meilisearch   │
│   tickers       macro themes   citations      Redis pub     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────── REPORT GENERATION ───────────────────────┐
│                                                              │
│   wiki/* updates (concept, entity, source pages)             │
│   Processed/Report of news/YYYY-MM-DD.md                     │
│   Processed/MASTER Report/YYYY-MM-DD.md                      │
│              │                                               │
│              ▼ (Puppeteer)                                   │
│   Processed/**/*.pdf  ─── institutional PDF                  │
│              │                                               │
│              ▼                                               │
│   raw/old news/YYYY-MM-DD/  ◀── move processed clippings     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────── DELIVERY ────────────────────────────┐
│                                                              │
│   FastAPI ──REST──▶ Next.js dashboard                        │
│      │      WS                                               │
│      └────────────▶ real-time event stream                   │
│                                                              │
│   Meilisearch ◀──── /search                                  │
│   pgvector    ◀──── /search/semantic, /graph                 │
│   PDF blobs   ◀──── /reports/:id/pdf                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Service inventory

| Service | Port | Responsibility |
|---|---|---|
| `web` (Next.js) | 3000 | Dashboard, SSR, edge auth |
| `api` (FastAPI) | 8000 | REST + WebSocket gateway |
| `worker` (Celery + LangGraph) | — | AI pipeline execution |
| `watcher` (Python) | — | Vault file events → Redis Stream |
| `pdf` (Puppeteer + Node) | 4000 | Headless PDF rendering microservice |
| `postgres` | 5432 | Relational + pgvector |
| `redis` | 6379 | Cache, queue broker, pub/sub |
| `meili` | 7700 | Full-text + hybrid search |

## Data plane

```
raw/news (markdown)  ──► Postgres `news_items`     ◀── source of truth
                     ──► Postgres `entities`       ◀── companies, tickers
                     ──► Postgres `embeddings`     ◀── pgvector (3072d)
                     ──► Meilisearch `news`        ◀── search index
                     ──► wiki/* (markdown)         ◀── human-readable knowledge
                     ──► Processed/* (md + pdf)    ◀── institutional reports
```

## Control plane

- **Trigger**: filesystem event in `raw/news/`
- **Bus**: Redis Streams (`ingest`, `enrich`, `report`)
- **Orchestrator**: LangGraph state machine, persisted in Postgres
- **Scheduler**: Celery Beat — daily 06:00 ICT report build, weekly 07:00 Monday
- **Realtime fanout**: Redis Pub/Sub → API WebSocket → dashboard

## Failure modes & recovery

- **LLM call failure** — exponential backoff (3 retries), fallback model, then DLQ
- **Vault drift** — periodic full reconcile job (hourly) cross-checks DB vs filesystem
- **PDF render timeout** — fall back to client-side `@react-pdf/renderer`
- **Embedding cost spike** — cache by content hash; reuse for identical clippings
- **Pipeline poison message** — write to `pipeline_dead_letters` table + Slack alert

## Security model

- API: JWT (HS256) for human users, mTLS for worker ↔ api
- Vault filesystem mounted read-only into `api`, read-write only in `worker`
- Secrets: 1Password Connect or HashiCorp Vault — never in `.env` in prod
- LLM PII: redaction layer before sending Vietnamese personal data to external LLMs

## Scalability strategy

| Pressure point | Mitigation |
|---|---|
| Burst of clippings | Redis Stream consumer group, parallel workers |
| Long-context Claude calls | Chunk + map-reduce summarizer |
| Embedding QPS | Batched calls (16/req), Redis content-hash cache |
| Search latency | Meili replica + pgvector HNSW index |
| Dashboard fanout | WebSocket sharded by `user_id mod N` |
