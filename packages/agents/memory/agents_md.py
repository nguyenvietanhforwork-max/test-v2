"""Read / append-only writes to AGENTS.md — the operational memory file.

AGENTS.md is the system's lean, structured rolling log + schemas. Agents read
it on every run for operational facts (industry list, frontmatter schema,
recent decisions). Writes are append-only with a timestamp header.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings  # type: ignore[import-not-found]

AGENTS_MD = Path(settings.VAULT_RAW).parent / "AGENTS.md"


def read() -> str:
    if not AGENTS_MD.exists():
        return ""
    return AGENTS_MD.read_text(encoding="utf-8")


def append_decision(actor: str, kind: str, body: str) -> None:
    """Append a timestamped entry under `## Operational Log`."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"\n\n### {ts} · {actor} · {kind}\n\n{body.rstrip()}\n"
    with AGENTS_MD.open("a", encoding="utf-8") as f:
        f.write(entry)
