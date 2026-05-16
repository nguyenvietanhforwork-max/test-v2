"""Vault watcher entrypoint.

Strategy:
  • watchdog observers for raw/news, raw/PDF Files, raw/Social Media Post
  • debounce 250ms per file (handles editor save bursts)
  • content-hash de-dupe before POSTing to API
  • periodic full rescan every 5 minutes as safety net
  • subscribes to Redis 'control.rescan' to handle manual /v1/refresh
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from pathlib import Path

import httpx
import structlog
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from ingestion.config import settings
from ingestion.parsers import parse_file
from ingestion.redis_bus import subscribe_control

log = structlog.get_logger()

WATCHED_SUBDIRS = ["news", "PDF Files", "Social Media Post"]
SEEN_HASHES: set[str] = set()
DEBOUNCE: dict[str, asyncio.TimerHandle] = {}


class Handler(FileSystemEventHandler):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    def on_created(self, event):  # noqa: D401
        if event.is_directory:
            return
        path = event.src_path
        existing = DEBOUNCE.pop(path, None)
        if existing:
            existing.cancel()
        DEBOUNCE[path] = self.loop.call_later(
            0.25, lambda: asyncio.run_coroutine_threadsafe(_process(path), self.loop)
        )

    on_modified = on_created  # treat modify same as create (Web Clipper updates frontmatter)


async def _process(path_str: str) -> None:
    path = Path(path_str)
    if not path.exists():
        return
    if path.suffix.lower() not in {".md", ".pdf", ".html"}:
        return
    try:
        record = parse_file(path)
    except Exception as e:
        log.exception("ingest.parse_failed", path=str(path), error=str(e))
        return
    if record["content_hash"] in SEEN_HASHES:
        return
    SEEN_HASHES.add(record["content_hash"])

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(f"{settings.api_base_url}/v1/ingest", json=record)
            resp.raise_for_status()
            log.info("ingest.ok", path=str(path), id=resp.json().get("id"))
        except httpx.HTTPError as e:
            log.error("ingest.api_failed", path=str(path), error=str(e))
            SEEN_HASHES.discard(record["content_hash"])  # retry on next scan


async def full_scan(root: Path) -> None:
    """Belt-and-braces scan, runs every 5 minutes."""
    for sub in WATCHED_SUBDIRS:
        d = root / sub
        if not d.exists():
            continue
        for f in d.rglob("*"):
            if f.is_file():
                await _process(str(f))


async def periodic_scan(root: Path) -> None:
    while True:
        await asyncio.sleep(300)
        log.info("ingest.full_scan.start")
        await full_scan(root)


async def main() -> None:
    root = Path(settings.vault_path) / settings.vault_raw_dir
    root.mkdir(parents=True, exist_ok=True)
    log.info("watcher.start", root=str(root))

    loop = asyncio.get_running_loop()
    observer = Observer()
    handler = Handler(loop)
    for sub in WATCHED_SUBDIRS:
        d = root / sub
        d.mkdir(parents=True, exist_ok=True)
        observer.schedule(handler, str(d), recursive=True)
    observer.start()

    try:
        # initial scan
        await full_scan(root)
        # background scan loop + redis control listener
        await asyncio.gather(periodic_scan(root), subscribe_control(_process, root))
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    asyncio.run(main())
