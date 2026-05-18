"""Ingest service — manual triggers + helper for the pipeline."""

from __future__ import annotations

from uuid import uuid4

import redis.asyncio as redis_asyncio

from app.core.config import settings


async def trigger_full_rescan() -> str:
    """Push a `reconcile` event onto the Redis Stream so the worker picks it up."""
    job_id = str(uuid4())
    client = redis_asyncio.from_url(settings.REDIS_URL, decode_responses=True)
    await client.xadd("ingest", {"kind": "reconcile", "job_id": job_id})
    await client.aclose()
    return job_id
