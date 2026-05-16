# Atlas — Data & Event Flow

## 1. End-to-end ingest sequence

```
┌──────────┐       ┌──────────┐      ┌─────────┐       ┌────────┐      ┌────────┐      ┌────────┐
│  vault   │       │ watcher  │      │  redis  │       │ worker │      │   db   │      │   api  │
│   FS     │       │          │      │ stream  │       │(lang-  │      │  +pg   │      │  + WS  │
└────┬─────┘       └────┬─────┘      └────┬────┘       └───┬────┘      └───┬────┘      └───┬────┘
     │ FileCreated      │                 │                │               │               │
     │ raw/news/x.md    │                 │                │               │               │
     ├─────────────────▶│ on_created      │                │               │               │
     │                  │  parse fm       │                │               │               │
     │                  │  hash content   │                │               │               │
     │                  │  XADD ingest    │                │               │               │
     │                  ├────────────────▶│                │               │               │
     │                  │                 │ XREADGROUP     │               │               │
     │                  │                 │◀──────────────┤               │               │
     │                  │                 │                │ extract       │               │
     │                  │                 │                ├──────────────▶│ INSERT items  │
     │                  │                 │                │ classify      │               │
     │                  │                 │                ├──────────────▶│ UPSERT inds   │
     │                  │                 │                │ summarize     │               │
     │                  │                 │                │ embed         │               │
     │                  │                 │                ├──────────────▶│ INSERT emb    │
     │                  │                 │                │ persist       │               │
     │                  │                 │                ├──────────────▶│ COMMIT        │
     │                  │                 │                │ publish       │               │
     │                  │                 │                ├──PUBLISH─────▶│               │
     │                  │                 │                │  events:user  │               │
     │                  │                 │                │               │ SUBSCRIBE     │
     │                  │                 │                │               │◀──────────────┤
     │                  │                 │                │               │ WS push       │
     │                  │                 │                │               │ news.created  │
     │                  │                 │                │               │──────────────▶│ dashboard
```

## 2. Event types

```ts
type Event =
  | { type: 'news.created'; payload: NewsItem }
  | { type: 'news.updated'; payload: NewsItem }
  | { type: 'report.published'; payload: Report }
  | { type: 'pipeline.step'; payload: { runId: string; step: PipelineStep; status: 'started'|'done'|'failed'; latencyMs?: number; tokens?: number } }
  | { type: 'pipeline.failed'; payload: { runId: string; error: string } }
  | { type: 'vault.reconciled'; payload: { added: number; updated: number; missing: number } }
  | { type: 'embedding.done'; payload: { newsId: string } };
```

Channel naming:
- `events:user:<user_id>` — per-user fanout
- `events:global` — all users (for system events)
- `events:debug` — verbose, dev-only

## 3. Daily brief build sequence

```
06:00 ICT cron tick (Celery Beat)
  │
  ▼
celery.task: build_daily_brief(date=today)
  │
  ├─► SELECT news_items WHERE date(published) = today
  ├─► SELECT report.previous_master FOR delta
  ├─► call agents.thesis_generator(items) → daily thesis
  ├─► call agents.summarizer(items, group_by=industry) → sections
  ├─► render markdown → Processed/Report of news/YYYY-MM-DD.md
  ├─► call pdf.render(markdown) → Processed/Report of news/YYYY-MM-DD.pdf
  ├─► INSERT reports row + report_sections + report_sources
  ├─► PUBLISH events:global { type:'report.published' }
  └─► move raw/news/* into raw/old news/YYYY-MM-DD/ (atomic mv)
```

## 4. WebSocket connection lifecycle

```
client                              api                             redis
  │                                  │                                │
  │ GET /ws/stream  (auth: bearer)   │                                │
  ├─────────────────────────────────▶│                                │
  │                                  │ jwt verify                     │
  │                                  │ SUBSCRIBE events:user:<id>     │
  │                                  ├───────────────────────────────▶│
  │ ◀── handshake ack ───────────────┤                                │
  │                                  │                                │
  │ ◀── event: pipeline.step ────────┤◀── message ────────────────────┤
  │ ◀── event: news.created ─────────┤◀── message ────────────────────┤
  │                                  │                                │
  │ ping (heartbeat 30s) ────────────┤                                │
  │ ◀── pong ────────────────────────┤                                │
  │                                  │                                │
  │ (disconnect)                     │ UNSUBSCRIBE                    │
  ├──────────────────────────────────▶───────────────────────────────▶│
```

Reconnect: client uses exponential backoff (1s → 30s cap) with jitter. Last-Event-ID header for replay (Redis Stream `XREAD`).

## 5. Failure & retry

```
pipeline_step (LangGraph node)
  │
  ▼
try:
   result = node.invoke(state)
except TransientError:    # HTTP 5xx, timeout, ratelimit
   retry with expo backoff (1, 4, 16 s), max 3
except SchemaError:        # LLM returned bad JSON
   reprompt with schema correction, max 2
except HardError:          # vault path missing, db connection lost
   raise
finally:
   emit pipeline.step event (done|failed)
   record pipeline_steps row (latency, tokens, model)

on terminal failure:
   INSERT INTO pipeline_dead_letters (run_id, payload, error, traceback)
   PUBLISH events:global { type: 'pipeline.failed', payload }
```

## 6. Reconciliation job

Hourly Celery Beat job:

1. Walk `raw/news/**/*.md` → set A (path, mtime, hash).
2. `SELECT path, content_hash FROM news_items` → set B.
3. Diff:
   - In A not B → enqueue ingest (missed).
   - In B not A → mark `news_items.archived = TRUE` (assume manual move).
   - Hash mismatch → enqueue re-ingest.
4. Walk `wiki/**/*.md` → reconcile `wiki_pages` table.
5. Emit `vault.reconciled` event.

## 7. Backpressure

- Redis Stream `MAXLEN ~ 10000` (approximate trimming).
- Worker concurrency: `CELERY_WORKER_CONCURRENCY=4` per pod; auto-scale on queue depth.
- If queue depth > 1000, watcher pauses for 5s before XADD (`STREAM_PRESSURE_THRESHOLD`).
- LLM provider rate limits handled by `tenacity`-backed wrappers in `packages/agents/models/`.
