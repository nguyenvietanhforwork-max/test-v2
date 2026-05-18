"""Listens for control.rescan events from the API (POST /v1/refresh)."""

import asyncio
from pathlib import Path

import redis.asyncio as redis
import structlog

from ingestion.config import settings

log = structlog.get_logger()


async def subscribe_control(process_fn, root: Path) -> None:
    r = redis.from_url(settings.redis_url, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("control.rescan")
    try:
        async for msg in pubsub.listen():
            if msg["type"] != "message":
                continue
            log.info("control.rescan.received")
            # iterate files
            for sub in ("news", "PDF Files", "Social Media Post"):
                d = root / sub
                if not d.exists():
                    continue
                for f in d.rglob("*"):
                    if f.is_file():
                        await process_fn(str(f))
    finally:
        await pubsub.unsubscribe()
        await r.aclose()
