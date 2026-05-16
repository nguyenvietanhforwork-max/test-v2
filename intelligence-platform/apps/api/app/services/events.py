"""Redis Streams publishers for the event-driven backbone."""

import json
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

_client: redis.Redis | None = None


def client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def publish_event(type_: str, data: dict[str, Any]) -> None:
    stream = "events.news" if type_.startswith("news.") else "events.reports"
    await client().xadd(stream, {"v": "1", "type": type_, "data": json.dumps(data)})
