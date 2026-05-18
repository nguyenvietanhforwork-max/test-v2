# n8n workflows

Three workflows ship with the platform. Import each JSON file via the n8n UI
(*Workflows → Import from File*) or via the n8n API:

```bash
for f in n8n/workflows/*.json; do
  curl -X POST "$N8N_HOST/rest/workflows" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    -H "Content-Type: application/json" \
    --data @"$f"
done
```

## Required environment variables (set in n8n's Settings → Environment)

| Var | Example |
|---|---|
| `API_BASE_URL` | `https://api.example.com` |
| `AGENTS_BASE_URL` | `https://agents.example.com` |
| `INTERNAL_SECRET_HMAC` | (HMAC the API expects, see `apps/api/app/core/security.py`) |

## Workflows

### `ingest-news`
- **Trigger:** webhook `POST /webhook/ingest-news`
- **Body:** `{ news_item_id, pipeline_run_id }` (the API posts this)
- **Flow:** calls `agents/run` → branches on error count → notifies API or DLQs after a 30s wait

### `daily-report`
- **Trigger:** cron `0 6 * * *` (Asia/Ho_Chi_Minh)
- **Flow:** calls `agents/build-report` with `type=master` → notifies API on success

### `weekly-wiki-lint`
- **Trigger:** cron `0 22 * * 0`
- **Flow:** calls `agents/wiki-lint` (long-running) — produces `outputs/lint-YYYY-MM-DD.md`

## Local test

With the docker-compose stack up:
```bash
curl -X POST http://localhost:5678/webhook/ingest-news \
  -H "Content-Type: application/json" \
  -d '{"news_item_id":"<uuid>","pipeline_run_id":"pr_test"}'
```
