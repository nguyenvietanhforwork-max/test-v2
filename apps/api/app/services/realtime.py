"""Realtime fanout — Redis pub/sub OR Supabase Realtime.

When `USE_SUPABASE_REALTIME=true` the dashboard subscribes directly to Supabase
postgres_changes events on the `news_item` and `report` tables. The API stops
publishing duplicate events to Redis to avoid double-fanout. This is the
recommended path for the Vercel + Supabase deployment.

When `USE_SUPABASE_REALTIME=false` (default), pipeline workers PUBLISH on
Redis channels which the FastAPI WebSocket gateway fans out.

Workers call `publish_event(channel, payload)`; the channel routing is the
same regardless of backend.
"""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis_asyncio
import structlog

from app.core.config import settings

log = structlog.get_logger()
_redis: redis_asyncio.Redis | None = None


async def publish_event(channel: str, payload: dict[str, Any]) -> None:
    """Idempotent publish — workers call this, transport is selected at runtime."""
    if settings.USE_SUPABASE_REALTIME:
        # Supabase Realtime is automatic for any INSERT into a tracked table.
        # The dashboard subscribes directly to `news_item` and `report` changes.
        # No-op here — we still log so it's visible in traces.
        log.debug("realtime.skip.redis", channel=channel, reason="supabase-direct")
        return

    global _redis
    if _redis is None:
        _redis = redis_asyncio.from_url(settings.REDIS_URL, decode_responses=True)
    await _redis.publish(channel, json.dumps(payload))
