"""Format dispatcher — returns the IngestRequest dict per file type."""

from pathlib import Path

from ingestion.parsers.markdown import parse_markdown
from ingestion.parsers.pdf import parse_pdf


def parse_file(path: Path) -> dict:
    suffix = path.suffix.lower()
    if suffix in {".md", ".html"}:
        return parse_markdown(path)
    if suffix == ".pdf":
        return parse_pdf(path)
    raise ValueError(f"unsupported file type: {suffix}")
