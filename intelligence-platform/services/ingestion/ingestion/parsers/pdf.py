"""PDF text extractor."""

import hashlib
from pathlib import Path

import pypdf

from ingestion.config import settings


def parse_pdf(path: Path) -> dict:
    reader = pypdf.PdfReader(str(path))
    text = "\n\n".join((page.extract_text() or "") for page in reader.pages)
    content_hash = "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
    rel = path.relative_to(settings.vault_path)
    return {
        "vault_path": str(rel).replace("\\", "/"),
        "content_hash": content_hash,
        "source_url": None,
        "title": (reader.metadata.title if reader.metadata else None) or path.stem,
        "publish_date": None,
        "raw_text": text,
        "language": "vi",
    }
