"""Periodic reconciliation: vault filesystem ↔ news_items table.

Catches drift caused by:
    - manual filesystem edits (someone copied files in without an event)
    - dropped events during watcher downtime
    - manual moves out of raw/news (mark archived)
    - content changes (re-ingest)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path

import redis.asyncio as redis_asyncio
import structlog
from sqlalchemy import select

from app.db.models import NewsItem  # type: ignore[import-not-found]
from app.db.session import async_session  # type: ignore[import-not-found]

log = structlog.get_logger()
VAULT_RAW_NEWS = Path(os.environ.get("VAULT_RAW", "/vault/raw")) / "news"
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")


async def reconcile_once() -> dict:
    redis = redis_asyncio.from_url(REDIS_URL, decode_responses=True)

    fs_map: dict[str, str] = {}
    for p in VAULT_RAW_NEWS.glob("*.md"):
        fs_map[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()

    added = 0
    rehashed = 0
    archived = 0

    async with async_session() as db:
        db_rows = (await db.execute(select(NewsItem.raw_path, NewsItem.content_hash, NewsItem.id))).all()
        db_map: dict[str, tuple[str, str]] = {r.raw_path: (r.content_hash, str(r.id)) for r in db_rows}

        # In FS, not in DB → enqueue
        for path, h in fs_map.items():
            if path not in db_map:
                await redis.xadd("ingest", {"kind": "ingest", "raw_path": path, "content_hash": h})
                added += 1
            elif db_map[path][0] != h:
                await redis.xadd("ingest", {"kind": "ingest", "raw_path": path, "content_hash": h, "rehash": "1"})
                rehashed += 1

        # In DB, not in FS → mark archived
        for path in db_map.keys() - fs_map.keys():
            row = (await db.execute(select(NewsItem).where(NewsItem.raw_path == path))).scalar_one()
            row.archived = True
            archived += 1
        await db.commit()

    summary = {"added": added, "rehashed": rehashed, "archived": archived}
    await redis.publish("events:global", json.dumps({"type": "vault.reconciled", "payload": summary}))
    await redis.aclose()
    log.info("reconcile.done", **summary)
    return summary


if __name__ == "__main__":
    print(asyncio.run(reconcile_once()))
