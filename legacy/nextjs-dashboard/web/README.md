# Atlas — Web (Next.js 14)

Frontend for the Atlas Intelligence Platform. Deployed to Vercel.

## Local dev

```bash
pnpm install
cp .env.example .env.local       # edit as needed
pnpm dev                         # http://localhost:3000
```

## Vercel deployment

**Repository:** monorepo. Root of the repo is the workspace; this app lives in `apps/web`.

When importing in Vercel:

1. **Root Directory** → `apps/web`
2. **Framework Preset** → Next.js (auto-detected)
3. **Build Command** → leave default (`pnpm build`)
4. **Install Command** → `pnpm install --no-frozen-lockfile`
5. **Environment Variables** (Project → Settings → Environment Variables):
   - `NEXT_PUBLIC_API_URL` → `https://<your-backend>/api/v1`
   - `NEXT_PUBLIC_WS_URL` → `wss://<your-backend>/ws/stream`
   - `NEXT_PUBLIC_USE_MOCKS` → `true` *(until the backend is live)*

The first deploy will be a preview URL like `atlas-<hash>.vercel.app`. Promote to production from the Vercel dashboard.

## Mocks fallback

When `NEXT_PUBLIC_USE_MOCKS=true`, server-side fetches in `lib/api.ts` return deterministic mock data instead of hitting the backend. This means the dashboard renders fully even before the FastAPI service exists.

To turn mocks off after wiring a real backend:

```
NEXT_PUBLIC_USE_MOCKS=false
NEXT_PUBLIC_API_URL=https://api.your-domain.com/api/v1
```

## CORS note

When the real backend is live, add the Vercel domain to `CORS_ORIGINS` in `apps/api/app/core/config.py`:

```python
CORS_ORIGINS = ["http://localhost:3000", "https://atlas.vercel.app", "https://atlas-<branch>.vercel.app"]
```
