"""Markdown / Obsidian Web Clipper parser.

Web Clipper writes frontmatter like:
---
title: ...
source: https://...
author: ...
published: 2026-05-15
tags: [news, finance]
---
"""

import hashlib
from datetime import date as date_
from pathlib import Path

import frontmatter

from ingestion.config import settings


def parse_markdown(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8", errors="replace")
    post = frontmatter.loads(raw)
    body = post.content
    content_hash = "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()

    publish_date = post.get("published") or post.get("date") or path.stat().st_mtime
    if isinstance(publish_date, (int, float)):
        publish_date = date_.fromtimestamp(publish_date)
    elif isinstance(publish_date, str):
        try:
            publish_date = date_.fromisoformat(publish_date[:10])
        except ValueError:
            publish_date = None

    rel = path.relative_to(settings.vault_path)
    return {
        "vault_path": str(rel).replace("\\", "/"),
        "content_hash": content_hash,
        "source_url": post.get("source") or post.get("url"),
        "title": post.get("title") or path.stem,
        "publish_date": publish_date.isoformat() if isinstance(publish_date, date_) else None,
        "raw_text": body,
        "language": "vi",  # detected downstream
    }
