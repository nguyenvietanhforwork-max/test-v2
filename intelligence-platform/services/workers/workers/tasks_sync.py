"""Sync tasks: archive raw files and clean up."""

import os
import shutil
from datetime import date
from pathlib import Path

import structlog
from celery import shared_task

log = structlog.get_logger()


@shared_task(name="workers.sync.archive_news_file")
def archive_news_file(vault_path: str) -> str:
    """Move /vault/raw/news/X.md → /vault/raw/old news/YYYY-MM-DD/X.md."""
    vault = Path(os.environ.get("VAULT_PATH", "/data/vault"))
    src = vault / vault_path
    if not src.exists():
        log.warning("archive.missing", path=str(src))
        return vault_path
    dst_dir = vault / "raw" / "old news" / date.today().isoformat()
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    shutil.move(str(src), str(dst))
    rel = dst.relative_to(vault)
    log.info("archive.ok", new_path=str(rel))
    return str(rel).replace("\\", "/")
