"""
scripts/summarize.py — cleaned/ → content/reports/.

Composes the same LangGraph nodes that packages/automation/pipeline/graph.py
runs in production, but synchronously, one document at a time, with no Celery
or Redis dependency. The idea: anyone with an API key can run this script and
get reports.

For each cleaned document:
  1. Run extraction (entities) — prompts/extraction/extract-entities.md
  2. Run classification (theme, industry) — prompts/extraction/* (TBD)
  3. Run summarization (topic_sentence + bullets) — prompts/summarization/topic-sentence-bullets.md
  4. Run scoring (signal, novelty) — prompts/scoring/signal-novelty.md
  5. Format as intelligence-letter — prompts/formatting/intelligence-letter.md
  6. Write to content/reports/YYYY-MM-DD-<slug>.md with full semantic frontmatter

USAGE
    python scripts/summarize.py                           # process all unsummarized cleaned/
    python scripts/summarize.py --date 2026-05-18         # only that date
    python scripts/summarize.py --file cleaned/foo.md     # specific file
    python scripts/summarize.py --dry-run                 # print the report, don't write

This is a SCAFFOLD. The LLM wiring is delegated to packages/agents/models/
which wraps Anthropic / OpenAI clients. Until ANTHROPIC_API_KEY is set,
the script writes a stub report with empty mini_report fields so the rest
of the pipeline can still be exercised.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import sys
import unicodedata
from datetime import datetime, timezone
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CLEANED = REPO_ROOT / "cleaned"
CONTENT_REPORTS = REPO_ROOT / "content" / "reports"
PROMPTS = REPO_ROOT / "prompts"

TEMPLATE_VERSION = "intelligence-letter@v2"
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "claude-sonnet-4-6")


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9-]+", "-", s).strip("-").lower()
    return s[:60] or "report"


def _load_cleaned(path: pathlib.Path) -> tuple[dict[str, str], str]:
    raw = path.read_text(encoding="utf-8")
    fm: dict[str, str] = {}
    body = raw
    if raw.startswith("---"):
        try:
            _, fm_block, body = raw.split("---", 2)
            for line in fm_block.splitlines():
                line = line.strip()
                if line.startswith("#") or ":" not in line:
                    continue
                k, _, v = line.partition(":")
                fm[k.strip()] = v.strip()
        except ValueError:
            pass
    return fm, body.strip()


def _llm_pipeline_stub(body: str) -> dict[str, Any]:
    """
    Placeholder for the actual extraction / classification / summarization /
    scoring chain. Returns the same shape the real pipeline does, with empty
    semantic content if no API key is available.

    Wire this to packages.automation.pipeline.graph when ready:
        from packages.automation.pipeline.graph import build_graph
        result = build_graph().invoke({"text": body, ...})
    """
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY"))
    return {
        "entities": [],
        "themes": [],
        "topics": [],
        "industry": "",
        "geography": [],
        "mini_report": {
            "topic_sentence": "" if has_key else "(stub — wire packages.automation.pipeline to populate)",
            "bullets": [] if has_key else [
                "<b>Stub:</b> connect this script to packages.automation.pipeline.graph.build_graph() to populate.",
                "<b>API key required:</b> set ANTHROPIC_API_KEY in .env",
                "<b>See:</b> prompts/summarization/topic-sentence-bullets.md for the editorial pattern.",
            ],
        },
        "signal_score": None,
        "novelty_score": None,
        "confidence": "low",
    }


def summarize_one(cleaned_path: pathlib.Path, *, dry_run: bool = False) -> pathlib.Path | None:
    fm, body = _load_cleaned(cleaned_path)
    pipeline = _llm_pipeline_stub(body)

    date = fm.get("cleaned_at", datetime.now(timezone.utc).isoformat())[:10]
    title = fm.get("title") or cleaned_path.stem.replace("-", " ").title()
    slug = _slug(title)
    report_id = f"report-{date}-{slug}"

    frontmatter = {
        "id": report_id,
        "type": "report",
        "kind": "daily-brief",
        "date": date,
        "title": title,
        "sources": [fm.get("source_path", str(cleaned_path.relative_to(REPO_ROOT)).replace("\\", "/"))],
        "industry": pipeline["industry"],
        "themes": pipeline["themes"],
        "topics": pipeline["topics"],
        "geography": pipeline["geography"],
        "entities": pipeline["entities"],
        "signal_score": pipeline["signal_score"],
        "novelty_score": pipeline["novelty_score"],
        "confidence": pipeline["confidence"],
        "prompt_version": "summarization/topic-sentence-bullets@v3",
        "model": DEFAULT_MODEL,
        "template_version": TEMPLATE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mini_report": pipeline["mini_report"],
    }

    # Render YAML by hand to avoid a yaml dep at runtime.
    def _yaml_dump(d: dict[str, Any], indent: int = 0) -> str:
        lines: list[str] = []
        pad = "  " * indent
        for k, v in d.items():
            if isinstance(v, dict):
                lines.append(f"{pad}{k}:")
                lines.append(_yaml_dump(v, indent + 1))
            elif isinstance(v, list):
                if not v:
                    lines.append(f"{pad}{k}: []")
                else:
                    lines.append(f"{pad}{k}:")
                    for item in v:
                        if isinstance(item, dict):
                            lines.append(f"{pad}  -")
                            lines.append(_yaml_dump(item, indent + 2))
                        else:
                            lines.append(f"{pad}  - {item!r}")
            elif v is None:
                lines.append(f"{pad}{k}: null")
            elif isinstance(v, (int, float, bool)):
                lines.append(f"{pad}{k}: {v}")
            else:
                # Quote strings that contain : or # to be safe
                s = str(v).replace("\n", " ")
                if any(c in s for c in ":#'\""):
                    s = '"' + s.replace('"', '\\"') + '"'
                lines.append(f"{pad}{k}: {s}")
        return "\n".join(lines)

    yaml_block = _yaml_dump(frontmatter)
    md = f"---\n{yaml_block}\n---\n\n# {title}\n\n{pipeline['mini_report']['topic_sentence']}\n\n"
    for b in pipeline["mini_report"]["bullets"]:
        md += f"- {b}\n"
    md += f"\n---\n\n**Source:** {frontmatter['sources'][0]}\n**Generated by:** `{frontmatter['prompt_version']}` on `{frontmatter['model']}`\n"

    if dry_run:
        print(md)
        return None

    CONTENT_REPORTS.mkdir(parents=True, exist_ok=True)
    out_path = CONTENT_REPORTS / f"{date}-{slug}.md"
    out_path.write_text(md, encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Only process cleaned files where the embedded date matches YYYY-MM-DD")
    parser.add_argument("--file", help="Process a specific cleaned/ file")
    parser.add_argument("--dry-run", action="store_true", help="Print report, don't write")
    args = parser.parse_args()

    if not CLEANED.exists():
        print(f"ERROR: {CLEANED} does not exist. Run `python scripts/clean.py` first.", file=sys.stderr)
        return 1

    if args.file:
        paths = [pathlib.Path(args.file)]
    else:
        paths = sorted(CLEANED.glob("*.md"))
        if args.date:
            paths = [p for p in paths if p.name.startswith(args.date)]

    count = 0
    for p in paths:
        out = summarize_one(p, dry_run=args.dry_run)
        if out:
            print(f"  → {out.relative_to(REPO_ROOT)}", file=sys.stderr)
        count += 1

    print(f"Processed {count} cleaned files.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
