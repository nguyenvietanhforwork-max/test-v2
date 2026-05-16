# Intelligence Platform

Production-grade AI intelligence operating system built on top of an Obsidian vault.
Ingests news, classifies it, generates institutional-grade reports, exports PDFs,
and serves a cinematic real-time dashboard.

## Architecture in 30 seconds

```
Obsidian Vault ──► Watcher ──► API ──► n8n ──► LangGraph Agents ──► Supabase (Postgres + pgvector)
                                                      │
                                                      ├─► PDF Engine (Puppeteer)
                                                      └─► Dashboard (Next.js, WebSocket)
```

Backend: **FastAPI + Python 3.12**
Orchestration: **n8n (visual workflows) + LangGraph (agent logic)**
DB: **Supabase Postgres + pgvector**
Frontend: **Next.js 15 App Router + Tailwind + shadcn/ui + Framer Motion**
Deploy: **Vercel (dashboard) + Railway (api/agents/workers/pdf) + Supabase (db) + Upstash (Redis)**

## Monorepo layout

```
intelligence-platform/
├── apps/
│   ├── dashboard/          # Next.js 15 frontend
│   └── api/                # FastAPI public API + WebSocket
├── services/
│   ├── agents/             # LangGraph agent graph (7 agents)
│   ├── ingestion/          # Vault watcher (watchdog) + parsers
│   ├── workers/            # Celery workers (background jobs)
│   └── pdf-engine/         # Node + Puppeteer + React-PDF
├── packages/
│   ├── shared-types/       # TS types shared with frontend
│   └── design-tokens/      # Tailwind preset, colors, motion
├── n8n/
│   └── workflows/          # Exported n8n workflow JSON
├── infra/
│   ├── supabase/migrations # SQL migrations (schema + pgvector + RLS)
│   ├── railway/            # Railway service configs
│   ├── vercel/             # Vercel project config
│   └── docker/             # docker-compose for local dev
├── obsidian/
│   └── plugin/             # Companion Obsidian plugin
└── docs/
    ├── ARCHITECTURE.md     # ◄── start here
    ├── DEPLOYMENT.md
    └── ROADMAP.md
```

## Start here

1. Read `docs/ARCHITECTURE.md`
2. `cp .env.example .env` and fill in keys
3. `docker compose -f infra/docker/docker-compose.yml up` (local dev)
4. Run Supabase migrations: `supabase db push` (or paste SQL into Supabase SQL editor)
5. Open the dashboard at http://localhost:3000

## Implementation order (MVP → scale)

| Phase | Goal | Services online |
|------|------|-----------------|
| **Phase 0** | Vault → DB raw ingest | watcher, api, supabase |
| **Phase 1 (MVP)** | Classify + summarize + daily report | + agents, workers |
| **Phase 2** | Dashboard + WebSocket + filters | + dashboard |
| **Phase 3** | PDF center + search + knowledge graph | + pdf-engine, meilisearch |
| **Phase 4** | Wiki auto-enrichment + alerts | + wiki agent, notification worker |
| **Phase 5** | Scale: read replicas, multi-region, GPU embeddings | infra hardening |

See `docs/ROADMAP.md` for detailed acceptance criteria per phase.
