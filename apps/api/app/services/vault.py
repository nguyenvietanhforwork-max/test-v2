"""Vault service — status, drift, reconcile trigger."""

from __future__ import annotations

from uuid import uuid4

import redis.asyncio as redis_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import NewsItem, PipelineDeadLetter


async def status(db: AsyncSession) -> dict:
    total = (await db.execute(select(func.count()).select_from(NewsItem))).scalar_one()
    dlq = (await db.execute(select(func.count()).select_from(PipelineDeadLetter).where(PipelineDeadLetter.resolved_at.is_(None)))).scalar_one()

    client = redis_asyncio.from_url(settings.REDIS_URL, decode_responses=True)
    queue_depth = await client.xlen("ingest")
    await client.aclose()

    return {
        "files_total": total,
        "files_in_raw_news": 0,  # populated by watcher heartbeat
        "drift": {"in_fs_not_db": 0, "in_db_not_fs": 0, "hash_mismatch": 0},
        "pipeline": {"queue_depth": queue_depth, "dlq_count": dlq, "last_run_at": None},
    }


async def trigger_reconcile() -> str:
    job_id = str(uuid4())
    client = redis_asyncio.from_url(settings.REDIS_URL, decode_responses=True)
    await client.xadd("ingest", {"kind": "reconcile", "job_id": job_id})
    await client.aclose()
    return job_id
