"""Redis pub/sub event bus.

A thin wrapper that fans out Redis pub/sub messages into asyncio.Queue per WS connection.
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any

import redis.asyncio as redis_asyncio

from app.core.config import settings
from app.core.logging import log


class EventBus:
    def __init__(self) -> None:
        self._client: redis_asyncio.Redis | None = None
        self._pubsub: redis_asyncio.client.PubSub | None = None
        self._queues: dict[str, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)
        self._task: asyncio.Task | None = None

    async def connect(self) -> None:
        self._client = redis_asyncio.from_url(settings.REDIS_URL, decode_responses=True)
        self._pubsub = self._client.pubsub()
        self._task = asyncio.create_task(self._reader_loop())
        log.info("event_bus.connected")

    async def disconnect(self) -> None:
        if self._task:
            self._task.cancel()
        if self._pubsub:
            await self._pubsub.close()
        if self._client:
            await self._client.aclose()

    async def publish(self, channel: str, event: dict[str, Any]) -> None:
        assert self._client
        await self._client.publish(channel, json.dumps(event))

    async def subscribe(self, *channels: str) -> asyncio.Queue[dict[str, Any]]:
        assert self._pubsub
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=256)
        for ch in channels:
            await self._pubsub.subscribe(ch)
            self._queues[ch].add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue) -> None:
        for ch, qs in list(self._queues.items()):
            qs.discard(queue)
            if not qs and self._pubsub:
                await self._pubsub.unsubscribe(ch)

    async def _reader_loop(self) -> None:
        assert self._pubsub
        while True:
            msg = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg is None:
                continue
            try:
                payload = json.loads(msg["data"])
                ch = msg["channel"]
                for q in list(self._queues.get(ch, ())):
                    if not q.full():
                        q.put_nowait(payload)
            except Exception as e:
                log.error("event_bus.read_error", error=str(e))


event_bus = EventBus()
