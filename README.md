# Atlas Intelligence Platform

**Production-grade AI intelligence platform** for Vietnamese / international macro & corporate news, built on top of the existing Obsidian knowledge vault. Hedge-fund-grade morning briefs, automatic classification, semantic search, knowledge graph, and a cinematic real-time dashboard.

> Codename: **Atlas** — the v2 evolution of the Value Research Vault.
> The legacy single-file `index.html` dashboard and `news_database.json` continue to work; Atlas wraps them with a real backend, real-time pipeline, and a production-grade frontend.

---

## 1 · What this is

A full system that turns the daily flow of news (clipped via Obsidian Web Clipper) into:

- structured, classified, embedded knowledge inside the `wiki/` layer
- institutional-quality daily/weekly intelligence reports (Markdown + PDF)
- a live dashboard with trace-back to original sources
- a semantic search + knowledge graph over every entity, industry and macro theme

The platform is **event-driven**: dropping a new clipping into `raw/news/` triggers the full ingest → classify → enrich → report → publish pipeline automatically. The dashboard updates in real-time over WebSockets.

---

## 2 · Repository layout (v2)

```
.
├── apps/
│   ├── web/                 Next.js 14 (App Router) — the dashboard
│   └── api/                 FastAPI — REST + WebSocket gateway
├── packages/
│   ├── automation/          Watchdog + LangGraph + Temporal workers
│   ├── agents/              AI agent definitions, prompts, tools
│   └── shared/              Pydantic + TS shared types, schemas
├── infra/
│   ├── docker/              Dockerfiles for each service
│   ├── compose/             docker-compose stacks (dev, prod)
│   └── k8s/                 Kubernetes manifests (prod)
├── docs/
│   ├── architecture.md      System architecture (full)
│   ├── data-flow.md         Event flow + sequence diagrams
│   ├── api.md               REST + WS endpoint reference
│   ├── ui-design-system.md  Design tokens, components, motion
│   └── deployment.md        Prod deployment playbook
├── demo/
│   └── dashboard.html       Live single-file UI/UX demo (open in browser)
│
│   --- Legacy / vault layer (unchanged) ---
├── raw/                     Obsidian vault — IMMUTABLE source data
├── wiki/                    Obsidian vault — AI-owned knowledge layer
├── Processed/               Generated reports (md + pdf)
├── _templates/              Markdown templates
├── outputs/                 Lint reports, exports, one-off artifacts
├── AGENTS.md                Agent operational memory + schemas
├── ARCHITECTURE.md          Top-level architecture summary
├── CLAUDE.md                Project instructions for Claude
├── index.html               Legacy single-file dashboard (still works)
├── news_database.json       Legacy index
└── docker-compose.yml       Full-stack quick start
```

## 3 · Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | **Next.js 14** (App Router), Tailwind, shadcn/ui, Framer Motion | Server components, motion-rich UI, design-system primitives |
| Backend | **FastAPI** + Uvicorn + Pydantic v2 | Async, type-first, WebSocket-native |
| DB | **Postgres 16** + **pgvector** | Relational + vector in one engine |
| Search | **Meilisearch** | Sub-50ms hybrid search, Vietnamese tokenizer |
| Cache / queue | **Redis 7** | Pub/sub for WS broadcast + Celery broker |
| Orchestration | **LangGraph** + **Temporal** | Durable, retryable AI workflows |
| File watcher | **watchdog** + **chokidar** fallback | Real-time vault sync |
| LLMs | Anthropic Claude (primary), OpenAI (fallback) | Vietnamese fluency, long context |
| Embeddings | `text-embedding-3-large` | 3072-dim, multilingual |
| PDF | **Puppeteer** (server) + **@react-pdf/renderer** (client) | Pixel-perfect institutional reports |
| Realtime | WebSockets + Server-Sent Events | Push pipeline events into dashboard |
| Deploy | Docker Compose (dev) → Kubernetes (prod) | Stateless services, horizontal scale |

## 4 · 60-second quick start

```bash
# 1. configure
cp .env.example .env

# 2. boot the full stack
docker compose up -d

# 3. open the dashboard
open http://localhost:3000

# 4. drop a markdown clipping into ./raw/news/
#    → watch it appear on the dashboard in real time
```

Want a quick visual preview without booting anything? Open **`demo/dashboard.html`** — single-file, no build, full UI/UX showcase with realistic mock data.

## 5 · Documents to read next

1. [`ARCHITECTURE.md`](./ARCHITECTURE.md) — one-page system overview
2. [`docs/architecture.md`](./docs/architecture.md) — full architecture (services, data plane, control plane)
3. [`docs/data-flow.md`](./docs/data-flow.md) — event flow diagrams + sequence
4. [`docs/ui-design-system.md`](./docs/ui-design-system.md) — design tokens, motion, components, accessibility
5. [`docs/api.md`](./docs/api.md) — REST + WS endpoint reference
6. [`docs/deployment.md`](./docs/deployment.md) — prod deployment playbook
7. [`demo/dashboard.html`](./demo/dashboard.html) — open in browser for the live UI demo

## 6 · System invariants

- `raw/` is **immutable**. Never written to by AI agents.
- `wiki/` is **AI-owned**. Humans review, agents mutate.
- Every wiki page carries YAML frontmatter; see `CLAUDE.md`.
- `AGENTS.md` is operational memory — keep it lean, link out to wiki.
- Every report cites its sources back to `raw/` paths.
- Industry folders auto-spawn — see `packages/agents/classifier`.
