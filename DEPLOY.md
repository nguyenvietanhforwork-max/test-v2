# Atlas — Deployment Guide

**Target stack:** GitHub → Supabase → Vercel (frontend) + Render or Railway (backend).
**Time:** ~25 minutes end-to-end. Cost: $0/month on free tiers.

GitHub user: **`nguyenvietanhforwork-max`** — exact commands below.

---

## TL;DR — the 5-step path

1. **Push to GitHub** → `nguyenvietanhforwork-max/atlas` (3 min)
2. **Provision Supabase** → Postgres + pgvector + Storage + Realtime (5 min)
3. **Deploy frontend to Vercel** → `apps/web/` with mocks first (5 min)
4. **Deploy backend to Render** → FastAPI + worker + beat + PDF service (8 min)
5. **Wire frontend → backend** → flip env vars, redeploy (2 min)

---

## 1 · Push to GitHub

Open PowerShell at the repo root: `E:\Application downloads\Value`

```powershell
git init -b main
git add .
git commit -m "Atlas v0.1 — initial scaffold"
git remote add origin https://github.com/nguyenvietanhforwork-max/atlas.git
git push -u origin main
```

If the remote already exists (you created it on github.com first), skip the `git remote add` line.

**If you haven't created the repo on GitHub yet**: open https://github.com/new, owner = `nguyenvietanhforwork-max`, repo name = `atlas`, **don't** add a README or .gitignore (we already have them), then run the four commands above.

> Privacy note: `raw/` (your Obsidian clippings) and `wiki/` (AI-owned knowledge) are currently tracked. If any of that is private, add them to `.gitignore` BEFORE the first push.

---

## 2 · Provision Supabase

1. Open https://supabase.com/dashboard → **New Project**
2. Name `atlas`, region **Southeast Asia (Singapore)** for VN latency, generate a strong DB password (save it).
3. Wait ~2 min for provisioning.
4. **Database extensions** → SQL Editor → run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   ```
5. **Storage** → create a public bucket named `atlas-pdfs`.
6. Grab the credentials you'll need next (Settings → API + Settings → Database):

   | Where to copy | Variable name |
   |---|---|
   | Settings → Database → **Connection string → URI (Transaction pooler, port 6543)** | `SUPABASE_DB_URL` |
   | Settings → API → **Project URL** | `SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_URL` |
   | Settings → API → **anon public** | `NEXT_PUBLIC_SUPABASE_ANON_KEY` |
   | Settings → API → **service_role secret** | `SUPABASE_SERVICE_ROLE_KEY` |

**Important:** the **Transaction pooler** URL (port 6543) is what you want for stateless workloads (Render/Railway/Vercel). The direct connection (port 5432) is fine for migrations but will exhaust pool size in serverless.

---

## 3 · Deploy frontend to Vercel

Open https://vercel.com/new.

1. **Import Git Repository** → pick `nguyenvietanhforwork-max/atlas`.
2. **Configure**:
   - **Project Name**: `atlas`
   - **Framework Preset**: Next.js (auto-detected — keep)
   - **Root Directory**: click **Edit** → set to `apps/web` ← **monorepo, don't skip**
   - **Install Command**: `pnpm install --no-frozen-lockfile`
   - **Build Command**: leave default (`pnpm build`)

3. **Environment Variables** (expand before deploying):

   | Key | Value | Scope |
   |---|---|---|
   | `NEXT_PUBLIC_USE_MOCKS` | `true` | All |
   | `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` *(swap after step 4)* | All |
   | `NEXT_PUBLIC_WS_URL` | `ws://localhost:8000/ws/stream` *(swap after step 4)* | All |
   | `NEXT_PUBLIC_SUPABASE_URL` | `https://<ref>.supabase.co` | All |
   | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGc…` | All |
   | `NEXT_PUBLIC_SITE_URL` | *(fill after first deploy)* | Production |

4. Click **Deploy**. First build is ~90s.
5. Visit the preview URL — dashboard should render the full UI with mock data.

---

## 4 · Deploy backend to Render

Render is the recommended path because the included `render.yaml` Blueprint creates the api + worker + beat + pdf services in one click.

1. Open https://dashboard.render.com → **New** → **Blueprint**
2. Connect GitHub → pick `nguyenvietanhforwork-max/atlas`
3. Render reads `render.yaml` and shows four services. Click **Apply**.
4. **Set the secrets** Render prompts you for (these have `sync: false` in the blueprint):
   - `SUPABASE_DB_URL` → from step 2.6 (the pooler URL)
   - `SUPABASE_URL` → from step 2.6
   - `SUPABASE_ANON_KEY` → from step 2.6
   - `SUPABASE_SERVICE_ROLE_KEY` → from step 2.6
   - `REDIS_URL` → see below ↓
   - `MEILI_HOST` → see below ↓
   - `MEILI_MASTER_KEY` → see below ↓
   - `ANTHROPIC_API_KEY` → https://console.anthropic.com
   - `OPENAI_API_KEY` → https://platform.openai.com

5. **Set up Redis** (Celery broker):
   - Open https://console.upstash.com → **Create Database** → region Singapore.
   - Copy the `redis://` connection string into `REDIS_URL` on every Render service that needs it.
6. **Set up Meilisearch**:
   - Option A: https://cloud.meilisearch.com → create instance, copy host + master key.
   - Option B: add a Render web service running `getmeili/meilisearch:v1.6`. Cheaper.
7. Wait for all services to deploy (~5 min). API URL will be like `https://atlas-api.onrender.com`.

**Alternative: Railway** — `apps/api/railway.json` is included. Create a project → Deploy from GitHub → it deploys `apps/api` with the Dockerfile + healthcheck. Add the worker as a second service with custom start command `celery -A packages.automation.worker.app worker --loglevel=info`.

**Alternative: Fly.io** — `fly.toml` at repo root. Run `fly launch` then `fly deploy`.

---

## 5 · Wire frontend → backend

Back in Vercel → Project → Settings → Environment Variables. **Update**:

| Key | New value |
|---|---|
| `NEXT_PUBLIC_USE_MOCKS` | `false` |
| `NEXT_PUBLIC_API_URL` | `https://atlas-api.onrender.com/api/v1` |
| `NEXT_PUBLIC_WS_URL` | `wss://atlas-api.onrender.com/ws/stream` |
| `NEXT_PUBLIC_SITE_URL` | `https://atlas.vercel.app` |

Then **Deployments** → ⋯ on the latest → **Redeploy**.

Also update CORS on the backend — Render → atlas-api → Environment:

```
CORS_ORIGINS=["https://atlas.vercel.app","https://atlas-git-main-<your-team>.vercel.app","http://localhost:3000"]
```

Render will redeploy the API automatically.

---

## 6 · Smoke test

1. Open `https://atlas.vercel.app` — dashboard loads.
2. Drop a markdown clipping into `raw/news/` on the Render worker's persistent disk (or commit it to GitHub and let Render redeploy). The watcher should fire and the dashboard should receive a `news.created` event via Supabase Realtime within ~5s.
3. Trigger the daily brief on demand:
   ```bash
   curl -X POST https://atlas-api.onrender.com/api/v1/reports/build \
        -H "Authorization: Bearer <jwt>" \
        -d '{"type": "daily"}'
   ```

---

## 7 · Common gotchas

**Build error: "Cannot find module 'tailwindcss-animate'"** → Vercel didn't install devDependencies. Project → Settings → set Install Command to `pnpm install --no-frozen-lockfile`.

**FastAPI: `psycopg.errors.UndefinedFunction: function hnsw...`** → forgot step 2.4 (the `CREATE EXTENSION` calls). Re-run them in Supabase SQL Editor.

**Realtime not firing on the dashboard** → confirm `USE_SUPABASE_REALTIME=true` on backend AND `NEXT_PUBLIC_SUPABASE_*` are set on Vercel AND Supabase → Database → Replication → `news_item` and `report` tables are enabled for Realtime.

**Worker crashes immediately** → almost always missing `SUPABASE_DB_URL` or `ANTHROPIC_API_KEY`. Check `render.yaml` envVars vs what's actually set in the dashboard.

**Vercel build hangs on pnpm** → if you're seeing lockfile errors, run `pnpm install` locally in `apps/web` and commit the resulting `pnpm-lock.yaml`.

**CORS errors in browser console** → CORS_ORIGINS on the backend must include the exact frontend origin including protocol and any preview subdomain.

---

## 8 · Cost estimate (free tier)

| Service | Free tier | Paid breakpoint |
|---|---|---|
| GitHub | unlimited public | — |
| Vercel | 100GB bandwidth | $20/mo Pro at ~250GB |
| Supabase | 500MB DB, 1GB storage, 50K MAU | $25/mo Pro at 8GB DB |
| Render | 750 hr/mo web | $7/mo per service for always-on |
| Upstash Redis | 10K commands/day | $0.20/100K beyond |
| Meilisearch Cloud | 100K docs | $30/mo at 1M docs |
| Anthropic Claude | pay-per-token | ~$0.003/1K input |
| OpenAI embeddings | pay-per-token | $0.13/1M tokens |

Realistic LLM spend for ~50 clippings/day: ≈ $8–15/month.

---

## 9 · After deploy — what to tweak

1. **Domain**: Vercel → Settings → Domains → add `atlas.yourdomain.com` and follow DNS instructions.
2. **Auth**: enable Supabase Auth, point `apps/api/app/core/security.py` at it (replace the custom JWT flow).
3. **Observability**: add Logflare/Better Stack — Render and Vercel both pipe logs natively.
4. **Backups**: Supabase auto-backups Postgres; you also want a daily restic backup of the vault filesystem.
5. **CI/CD**: GitHub Actions config is sketched in `docs/deployment.md` §6.
