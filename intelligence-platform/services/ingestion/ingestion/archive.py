"""Atomic move from raw/news → raw/old news/YYYY-MM-DD/.

Called by a Celery worker (services/workers/sync_worker.py) once the pipeline
marks an item as `reported`.
"""

import shutil
from datetime import date
from pathlib import Path

import structlog

from ingestion.config import settings

log = structlog.get_logger()


def archive(vault_path: str) -> str:
    """Move file from raw/news/... to raw/old news/YYYY-MM-DD/...
    Returns the new vault-relative path."""
    src = Path(settings.vault_path) / vault_path
    if not src.exists():
        log.warning("archive.missing", path=str(src))
        return vault_path

    today = date.today().isoformat()
    dst_dir = Path(settings.vault_path) / settings.vault_archive_dir / today
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name

    shutil.move(str(src), str(dst))  # atomic on same volume
    rel = dst.relative_to(settings.vault_path)
    log.info("archive.ok", from_=str(src), to=str(dst))
    return str(rel).replace("\\", "/")
