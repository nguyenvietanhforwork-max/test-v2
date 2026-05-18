"""
scripts/crawl.py — optional external-source crawler.

The primary ingest path is the Obsidian Web Clipper writing directly to
raw/news/. This script exists for the secondary path: pulling from RSS feeds
or specific URLs and depositing into raw/.

Default behavior: STUB — print "no crawl sources configured" and exit.

To wire it up:
  1. Create raw/.crawl-sources.yaml with:
       feeds:
         - url: https://vneconomy.vn/rss
           limit: 10
         - url: https://vietstock.vn/rss
           limit: 10
  2. Install feedparser:  pip install feedparser
  3. Run:  python scripts/crawl.py

USAGE
    python scripts/crawl.py [--dry-run]

Per AGENTS.md §2, this script only writes to raw/news/<today>/. It never
modifies existing raw/ files.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
from datetime import datetime

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_NEWS = REPO_ROOT / "raw" / "news"
SOURCES_CONFIG = REPO_ROOT / "raw" / ".crawl-sources.yaml"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not SOURCES_CONFIG.exists():
        print("No crawl sources configured.", file=sys.stderr)
        print(f"Create {SOURCES_CONFIG.relative_to(REPO_ROOT)} to enable crawling.", file=sys.stderr)
        print("See scripts/crawl.py docstring for the format.", file=sys.stderr)
        return 0

    try:
        import yaml  # type: ignore
        import feedparser  # type: ignore
    except ImportError as e:
        print(f"Missing dependency: {e}. Install with: pip install pyyaml feedparser", file=sys.stderr)
        return 1

    cfg = yaml.safe_load(SOURCES_CONFIG.read_text(encoding="utf-8"))
    today = datetime.now().date().isoformat()
    out_dir = RAW_NEWS / today

    fetched = 0
    for feed_cfg in (cfg.get("feeds") or []):
        url = feed_cfg["url"]
        limit = feed_cfg.get("limit", 10)
        parsed = feedparser.parse(url)
        for entry in parsed.entries[:limit]:
            title = entry.get("title", "untitled")
            slug = title.lower().replace(" ", "-")[:60]
            out = out_dir / f"{slug}.md"
            if out.exists():
                continue
            if args.dry_run:
                print(f"  would write: {out.relative_to(REPO_ROOT)}", file=sys.stderr)
                continue
            out_dir.mkdir(parents=True, exist_ok=True)
            md = f"---\ntitle: {title!r}\nurl: {entry.get('link', '')}\nsource: {parsed.feed.get('title', url)}\npublished: {entry.get('published', '')}\nclipped_at: {datetime.now().isoformat()}\n---\n\n{entry.get('summary', '')}\n"
            out.write_text(md, encoding="utf-8")
            fetched += 1

    print(f"Crawled {fetched} new items into raw/news/{today}/", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
