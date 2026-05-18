"""Celery tasks — thin wrappers that delegate to async pipeline code."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import redis as redis_sync
import structlog

from packages.automation.pipeline.graph import run_pipeline
from packages.automation.pipeline.state import PipelineState
from packages.automation.watcher.reconcile import reconcile_once
from packages.automation.worker.app import celery

log = structlog.get_logger()
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CONSUMER_GROUP = "atlas-workers"
CONSUMER_NAME = os.environ.get("HOSTNAME", "worker-1")


@celery.task(name="atlas.ingest.process_file", bind=True, max_retries=3, default_retry_delay=8)
def process_file(self, raw_path: str, content_hash: str) -> dict:
    """Run the full LangGraph pipeline for a single clipping."""
    try:
        return asyncio.run(_process(raw_path, content_hash))
    except Exception as exc:
        log.error("task.process_file.failed", path=raw_path, error=str(exc))
        raise self.retry(exc=exc) from exc


async def _process(raw_path: str, content_hash: str) -> dict:
    content = Path(raw_path).read_text(encoding="utf-8")
    state = PipelineState(
        raw_path=raw_path,
        content=content,
        content_hash=content_hash,
        job_id=f"job-{content_hash[:8]}",
    )
    final = await run_pipeline(state)
    return {
        "news_id": str(final.news_id) if final.news_id else None,
        "steps": final.step_history,
        "errors": final.errors,
        "tokens": final.total_tokens,
    }


@celery.task(name="atlas.ingest.drain_stream")
def drain_stream() -> dict:
    """Consume up to N events from Redis Stream `ingest` and dispatch tasks.

    Uses a consumer group so multiple worker pods share the load safely.
    """
    r = redis_sync.from_url(REDIS_URL, decode_responses=True)
    try:
        r.xgroup_create("ingest", CONSUMER_GROUP, id="0", mkstream=True)
    except redis_sync.exceptions.ResponseError:
        pass  # group exists

    msgs = r.xreadgroup(CONSUMER_GROUP, CONSUMER_NAME, {"ingest": ">"}, count=16, block=500) or []
    dispatched = 0
    for _stream, entries in msgs:
        for msg_id, fields in entries:
            kind = fields.get("kind", "ingest")
            if kind == "ingest":
                process_file.delay(fields["raw_path"], fields["content_hash"])
            elif kind == "reconcile":
                reconcile.delay()
            r.xack("ingest", CONSUMER_GROUP, msg_id)
            dispatched += 1
    return {"dispatched": dispatched}


@celery.task(name="atlas.maintenance.reconcile")
def reconcile() -> dict:
    return asyncio.run(reconcile_once())


@celery.task(name="atlas.reports.build_daily")
def build_daily() -> dict:
    """Build today's daily intelligence brief (markdown + PDF)."""
    from packages.automation.reporting.daily_brief import build_today
    return asyncio.run(build_today())


@celery.task(name="atlas.reports.build_weekly")
def build_weekly() -> dict:
    from packages.automation.reporting.weekly_synthesis import build_last_week
    return asyncio.run(build_last_week())
