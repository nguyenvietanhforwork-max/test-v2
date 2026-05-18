"""
scripts/clean.py — normalize raw clippings into cleaned/.

Reads raw/news/**/*.md and writes cleaned/<YYYY-MM-DD>-<slug>.md with:
  - HTML stripped
  - Web-clipper boilerplate removed (best-effort regex)
  - Encoding normalized (zero-width spaces, smart-quote consistency)
  - Frontmatter enriched: word_count, reading_time_minutes, language hint

raw/ is NEVER modified (AGENTS.md §2 invariant).

USAGE
    python scripts/clean.py                       # process all
    python scripts/clean.py --since 2026-05-18    # only clippings from that date forward
    python scripts/clean.py --force               # re-clean even if cleaned/ output exists
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
import unicodedata
from datetime import datetime
from typing import Iterable

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = REPO_ROOT / "raw" / "news"
CLEANED = REPO_ROOT / "cleaned"

# Web-clipper boilerplate patterns (extend as you encounter them):
BOILERPLATE_LINE_PATTERNS = [
    re.compile(r"^\s*(Bài viết liên quan|Đọc thêm|Tags?:|Bookmark|Chia sẻ|Share this article)\s*:?$", re.IGNORECASE),
    re.compile(r"^\s*Powered by .+$", re.IGNORECASE),
    re.compile(r"^\s*©\s*\d{4}.+$"),
    re.compile(r"^\s*\[\!\[.+\]\(.+\)\]\(.+\)\s*$"),  # nested-image link spam
]
ZERO_WIDTH = "​‌‍﻿"


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    for ch in ZERO_WIDTH:
        text = text.replace(ch, "")
    # Smart-quote → straight (preserves Vietnamese; only ASCII-adjacent quotes)
    text = (text
            .replace("“", '"').replace("”", '"')
            .replace("‘", "'").replace("’", "'"))
    return text


def strip_boilerplate(text: str) -> str:
    keep: list[str] = []
    for line in text.splitlines():
        if any(p.match(line) for p in BOILERPLATE_LINE_PATTERNS):
            continue
        keep.append(line)
    # Collapse 3+ blank lines to 2.
    out = "\n".join(keep)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def reading_time(words: int) -> int:
    return max(1, round(words / 220))  # 220 wpm for VN editorial reading


def detect_language(text: str) -> str:
    # Crude: presence of Vietnamese diacritics → 'vi', else 'en'.
    if re.search(r"[ăâđêôơưĂÂĐÊÔƠƯ]", text):
        return "vi"
    return "en"


def parse_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    try:
        _, fm, body = text.split("---", 2)
    except ValueError:
        return "", text
    return fm.strip(), body.strip()


def emit(src: pathlib.Path, dst: pathlib.Path) -> None:
    raw = src.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(raw)
    body = strip_boilerplate(normalize_text(body))
    words = len(body.split())
    lang = detect_language(body)

    enriched_fm_lines = [
        "---",
        f"source_path: {src.relative_to(REPO_ROOT).as_posix()}",
        f"cleaned_at: {datetime.now().isoformat(timespec='seconds')}",
        f"word_count: {words}",
        f"reading_time_minutes: {reading_time(words)}",
        f"language: {lang}",
    ]
    if fm:
        enriched_fm_lines.append("# original frontmatter:")
        for line in fm.splitlines():
            enriched_fm_lines.append(f"#   {line}")
    enriched_fm_lines.append("---\n")

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(enriched_fm_lines) + body + "\n", encoding="utf-8")


def iter_sources(since: str | None) -> Iterable[pathlib.Path]:
    if not RAW.exists():
        return iter(())
    files = sorted(RAW.rglob("*.md"))
    if since:
        since_dt = datetime.fromisoformat(since).date()
        files = [f for f in files if any(p == since_dt.isoformat() or p > since_dt.isoformat() for p in f.parts)]
    return files


def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9-]+", "-", s).strip("-").lower()
    return s[:80] if s else "untitled"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", help="Process only clippings from this date forward (YYYY-MM-DD)")
    parser.add_argument("--force", action="store_true", help="Re-clean even if output exists")
    args = parser.parse_args()

    CLEANED.mkdir(parents=True, exist_ok=True)
    count = 0
    skipped = 0
    for src in iter_sources(args.since):
        # date from parent directory if it looks like YYYY-MM-DD, else today
        date_part = next((p for p in src.parts if re.match(r"\d{4}-\d{2}-\d{2}", p)), datetime.now().date().isoformat())
        dst_name = f"{date_part}-{slugify(src.stem)}.md"
        dst = CLEANED / dst_name
        if dst.exists() and not args.force:
            skipped += 1
            continue
        emit(src, dst)
        count += 1
    print(f"Cleaned {count} files (skipped {skipped} already-clean).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
