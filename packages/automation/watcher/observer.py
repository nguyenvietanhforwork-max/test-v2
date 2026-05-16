"""File-system watcher → Redis Stream `ingest`.

Watches `$VAULT_RAW` for new clippings, normalizes them, hashes the content,
and pushes an event onto the Redis Stream `ingest`. Celery workers consume.

Run:
    python -m packages.automation.watcher.observer
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import signal
import sys
import time
from pathlib import Path

import redis.asyncio as redis_asyncio
import structlog
from watchdog.events import FileCreatedEvent, FileMovedEvent, FileSystemEventHandler
from watchdog.observers import Observer

log = structlog.get_logger()

VAULT_RAW = Path(os.environ.get("VAULT_RAW", "/vault/raw"))
WATCH_DIRS = [VAULT_RAW / "news", VAULT_RAW / "PDF Files", VAULT_RAW / "Social Media Post"]
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
STREAM = "ingest"
STREAM_MAXLEN = 10_000   # approximate trimming


class IngestHandler(FileSystemEventHandler):
    def __init__(self, loop: asyncio.AbstractEventLoop, redis: redis_asyncio.Redis) -> None:
        self.loop = loop
        self.redis = redis

    def on_created(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith((".md", ".pdf")):
            return
        asyncio.run_coroutine_threadsafe(self._enqueue(event.src_path), self.loop)

    def on_moved(self, event: FileMovedEvent):
        # Treat moves into the watch dir as creates (e.g. drag-drop)
        if event.is_directory:
            return
        if any(str(event.dest_path).startswith(str(d)) for d in WATCH_DIRS):
            asyncio.run_coroutine_threadsafe(self._enqueue(event.dest_path), self.loop)

    async def _enqueue(self, path: str) -> None:
        p = Path(path)
        try:
            # Wait for the file to settle (avoid partial writes)
            await asyncio.sleep(0.5)
            content = p.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            await self.redis.xadd(
                STREAM,
                {
                    "kind": "ingest",
                    "raw_path": str(p),
                    "size": str(len(content)),
                    "content_hash": digest,
                    "ts": str(time.time()),
                },
                maxlen=STREAM_MAXLEN,
                approximate=True,
            )
            log.info("watcher.enqueued", path=str(p), hash=digest[:12], bytes=len(content))
        except Exception as e:
            log.error("watcher.enqueue_failed", path=str(p), error=str(e))


async def main() -> None:
    redis = redis_asyncio.from_url(REDIS_URL, decode_responses=True)
    loop = asyncio.get_running_loop()
    handler = IngestHandler(loop, redis)
    observer = Observer()
    for d in WATCH_DIRS:
        d.mkdir(parents=True, exist_ok=True)
        observer.schedule(handler, str(d), recursive=False)
        log.info("watcher.watching", dir=str(d))
    observer.start()

    stop = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    log.info("watcher.started")

    await stop.wait()
    observer.stop()
    observer.join(timeout=5)
    await redis.aclose()
    log.info("watcher.stopped")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
