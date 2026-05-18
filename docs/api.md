# Atlas — API Reference

> Base URL: `https://api.atlas.local/api/v1` (dev: `http://localhost:8000/api/v1`)
> Auth: `Authorization: Bearer <jwt>` on every request.
> Errors: RFC 7807 problem details.

## 1. News

### `GET /news`

Query parameters:

| Param | Type | Notes |
|---|---|---|
| `date` | ISO date | Filter to a single day |
| `from`, `to` | ISO date | Range filter |
| `industry` | string slug | Comma-separated, OR'd |
| `entity` | string slug | Comma-separated, OR'd |
| `region` | `VN` \| `INT` | |
| `bucket` | `macro` \| `corp` | |
| `q` | string | Full-text (lexical) |
| `cursor` | base64 | Pagination cursor |
| `limit` | int (≤100) | Default 50 |

Response:

```json
{
  "items": [ { "id": "n_01...", "title": "...", "thesis": "...", "bullets": ["..."],
                "published_at": "2026-05-15T03:11:00Z", "source": {"name": "Reuters", "url": "https://..."},
                "industries": [{"slug": "banking", "name": "Banking"}],
                "entities":   [{"slug": "vingroup", "name": "Vingroup", "ticker": "VIC"}],
                "region": "VN", "bucket": "corp",
                "confidence": "high",
                "raw_path": "raw/news/2026-05-15--reuters--vingroup.md",
                "wiki_path": "wiki/Vietnam Enterprises/Real Estate/Vingroup.md" } ],
  "next_cursor": "..."
}
```

### `GET /news/:id`

Full record including raw markdown, citations, related items.

### `POST /news/refresh`

Manually trigger a vault scan. Returns 202 + `job_id`.

---

## 2. Reports

### `GET /reports`

| Param | Type |
|---|---|
| `type` | `daily` \| `weekly` \| `master` \| `industry` \| `entity` |
| `from`, `to` | ISO date |
| `industry`, `entity` | filter |

Returns paginated list with title, type, published_at, pdf_url, thesis.

### `GET /reports/:id`

```json
{
  "id": "r_01...",
  "type": "daily",
  "title": "Daily Intelligence Brief · 2026-05-15",
  "published_at": "2026-05-15T23:00:00Z",
  "thesis": "...",
  "markdown": "# ...",
  "sections": [
    { "id": "s_...", "heading": "Vietnam Macro", "body_md": "...",
      "sources": [ {"news_id": "n_...", "title": "...", "url": "..."} ] }
  ],
  "pdf_url": "/api/v1/reports/r_01.../pdf",
  "version": 3
}
```

### `GET /reports/:id/pdf`

Streams `application/pdf`. ETag set to content hash.

### `POST /reports/build`

Body: `{ "type": "industry", "industry": "banking", "from": "...", "to": "..." }` → 202 + `job_id`.

---

## 3. Entities

### `GET /entities/:slug`

```json
{
  "slug": "vingroup",
  "name": "Vingroup",
  "aliases": ["VIC", "Tập đoàn Vingroup"],
  "ticker": "VIC",
  "exchange": "HOSE",
  "industries": ["real-estate", "retail"],
  "country": "VN",
  "mentions_30d": 42,
  "sentiment_30d": 0.18,
  "wiki_path": "wiki/Vietnam Enterprises/Real Estate/Vingroup.md"
}
```

### `GET /entities/:slug/timeline`

Returns paginated news referencing the entity, ordered desc by `published_at`.

---

## 4. Industries

### `GET /industries`

List of 28+ industries with `mentions_7d`, `sentiment_7d`, `top_entities`.

### `GET /industries/:slug/heatmap`

Daily volume + sentiment for the last N days (default 30).

---

## 5. Search

### `POST /search`

Body:

```json
{
  "query": "Vingroup bond issuance",
  "mode": "hybrid",            // lexical | semantic | hybrid (default)
  "filters": {
    "industries": ["banking", "real-estate"],
    "from": "2026-04-01",
    "to": "2026-05-15"
  },
  "limit": 20
}
```

Response: ranked results with `score`, `match_type` (lex/sem), `highlights[]`.

---

## 6. Graph

### `GET /graph`

| Param | Type |
|---|---|
| `center` | entity or industry slug, optional |
| `depth` | int (1–3), default 2 |
| `window` | `24h` \| `7d` \| `30d` \| `all` |

Returns `{ nodes: [...], edges: [...] }` shaped for d3-force.

---

## 7. Vault

### `GET /vault/status`

```json
{
  "files_total": 1284,
  "files_in_raw_news": 12,
  "drift": { "in_fs_not_db": 0, "in_db_not_fs": 1, "hash_mismatch": 0 },
  "pipeline": { "queue_depth": 3, "dlq_count": 0, "last_run_at": "..." }
}
```

### `POST /vault/reconcile`

Triggers full diff; returns 202 + `job_id`.

---

## 8. WebSocket

### `GET /ws/stream`

Upgrade to WebSocket. Auth via `?token=<jwt>` query param or `Authorization` header on the upgrade request.

Server → client messages are JSON:

```json
{ "type": "news.created", "payload": { ...NewsItem } }
{ "type": "pipeline.step", "payload": { "run_id": "...", "step": "summarize", "status": "done", "latency_ms": 1842, "tokens": 1230 } }
{ "type": "report.published", "payload": { ...Report } }
```

Client → server: `{"type": "ping"}` every 30s. Server responds `{"type": "pong"}`.

Reconnect: send `Last-Event-ID` to resume from the last position in the Redis Stream.

---

## 9. Auth

### `POST /auth/login`

`{ "email": "...", "password": "..." }` → `{ "access_token": "...", "refresh_token": "..." }`

### `POST /auth/refresh`

`{ "refresh_token": "..." }` → new access token.

### `GET /auth/me`

Current user.

---

## 10. Error format

```json
{
  "type": "https://atlas.dev/errors/validation",
  "title": "Validation failed",
  "status": 422,
  "detail": "field `industry` must be one of [...]",
  "instance": "/api/v1/news?industry=foo",
  "trace_id": "01HX..."
}
```

Standard codes:

| Code | Meaning |
|---|---|
| 400 | Bad request |
| 401 | Missing / invalid auth |
| 403 | Authenticated but not allowed |
| 404 | Not found |
| 409 | Conflict (eg. content_hash already ingested) |
| 422 | Validation failed |
| 429 | Rate-limited |
| 500 | Server error (logged with trace_id) |
| 503 | Pipeline unhealthy |
