"""WebSocket fan-out backed by Redis pub/sub.

The API binds WebSocket connections, but the *source of truth* for events is
Redis so multiple API replicas all emit the same events. Workers and agents
publish to Redis; every API instance subscribes and pushes to its connected
sockets.
"""

import asyncio
import json
from typing import Any

import redis.asyncio as redis
import structlog
from fastapi import WebSocket

from app.core.config import settings

log = structlog.get_logger()

CHANNEL = "events:fanout"


class WsManager:
    def __init__(self) -> None:
        self._sockets: set[WebSocket] = set()
        self._task: asyncio.Task | None = None
        self._redis: redis.Redis | None = None

    async def start(self) -> None:
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        self._task = asyncio.create_task(self._listen())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
        if self._redis:
            await self._redis.aclose()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._sockets.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._sockets.discard(ws)

    async def broadcast(self, type_: str, data: dict[str, Any]) -> None:
        """Publish to Redis; every API replica will receive via _listen and push."""
        if not self._redis:
            return
        await self._redis.publish(CHANNEL, json.dumps({"type": type_, "data": data}))

    async def _listen(self) -> None:
        assert self._redis
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(CHANNEL)
        try:
            async for msg in pubsub.listen():
                if msg["type"] != "message":
                    continue
                payload = msg["data"]
                dead: list[WebSocket] = []
                for ws in self._sockets:
                    try:
                        await ws.send_text(payload)
                    except Exception:
                        dead.append(ws)
                for ws in dead:
                    self._sockets.discard(ws)
        except asyncio.CancelledError:
            await pubsub.unsubscribe(CHANNEL)
            raise


ws_manager = WsManager()
