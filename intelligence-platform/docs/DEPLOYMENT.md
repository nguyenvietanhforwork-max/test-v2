# Deployment guide

## Targets

| Component | Host | Build/runtime |
|---|---|---|
| `apps/dashboard` | Vercel | Next.js 15, Node 20 |
| `apps/api` | Railway | Python 3.12, FastAPI + uvicorn |
| `services/agents` | Railway | Python 3.12, FastAPI + LangGraph |
| `services/workers` | Railway (worker) | Python 3.12, Celery |
| `services/pdf-engine` | Railway | Node 20, Express + Puppeteer (uses `ghcr.io/puppeteer/puppeteer:latest` base) |
| `services/ingestion` | Railway (worker) or on-prem near vault | Python 3.12, watchdog |
| n8n | Railway (self-hosted) | docker image `n8nio/n8n` |
| Postgres + pgvector | Supabase | managed |
| Redis | Upstash | managed |
| Object storage | Supabase Storage | managed |

## First-time setup

```bash
# 1. Supabase
supabase login
supabase link --project-ref <your-ref>
supabase db push                     # applies infra/supabase/migrations/*

# 2. Upstash
upstash redis create intelligence-redis
# copy REDIS_URL to .env and to Railway env

# 3. Railway
railway login
railway init                          # in monorepo root
# For each service: railway up --service <name> with the railway.toml in infra/railway/<name>/

# 4. Vercel
vercel link --cwd apps/dashboard
vercel env pull apps/dashboard/.env.production.local

# 5. n8n
# Import workflows from n8n/workflows/*.json via the n8n UI.
```

## CI/CD

`.github/workflows/deploy.yml` (scaffolded under infra/) does:
1. Pull request → typecheck + tests + lint
2. Push to `main` → build affected services, deploy via Railway CLI
3. Vercel auto-deploys dashboard on push
4. Migrations: `supabase db push` runs in a manual-approval job

## Secrets to set per environment

```
DATABASE_URL, DATABASE_URL_SYNC
SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET
REDIS_URL
OPENAI_API_KEY, ANTHROPIC_API_KEY
N8N_WEBHOOK_URL, N8N_API_KEY
MEILISEARCH_HOST, MEILISEARCH_MASTER_KEY
```

## Smoke test (after deploy)

```bash
curl https://api.example.com/healthz
curl -X POST https://api.example.com/v1/refresh
curl https://api.example.com/v1/dashboard/today
```
