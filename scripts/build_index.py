"""
scripts/build_index.py — markdown → dashboard data feed.

Walks content/reports/*.md and content/wiki/*.md, validates against
schemas/report.schema.json, and emits the JSON files the dashboard consumes:

  - generated/index.json           — primary dashboard feed (matches the shape
                                      of the inlined ITEMS array in
                                      apps/dashboard/index.html)
  - generated/search-index.json    — Meilisearch loader payload
  - generated/embeddings-ready.json — queue for generate_embeddings.py

Per ADR-006, markdown is canonical and these JSON files are derived. Re-running
this script is idempotent.

USAGE
    python scripts/build_index.py              # build all
    python scripts/build_index.py --date 2026-05-18  # only that date
    python scripts/build_index.py --validate-only    # validate, don't write
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT_REPORTS = REPO_ROOT / "content" / "reports"
CONTENT_WIKI = REPO_ROOT / "content" / "wiki"
WIKI_FALLBACK = REPO_ROOT / "wiki"                  # hybrid alias from ADR-001
REPORTS_FALLBACK = REPO_ROOT / "Processed"          # pre-restructure location
GENERATED = REPO_ROOT / "generated"
SCHEMAS = REPO_ROOT / "schemas"

SCHEMA_VERSION = 1


def _resolve_reports_dir() -> pathlib.Path:
    """Pick the active reports directory under the hybrid model."""
    if CONTENT_REPORTS.exists():
        return CONTENT_REPORTS
    if REPORTS_FALLBACK.exists():
        return REPORTS_FALLBACK
    return CONTENT_REPORTS  # may be empty


def _resolve_wiki_dir() -> pathlib.Path:
    if CONTENT_WIKI.exists():
        return CONTENT_WIKI
    if WIKI_FALLBACK.exists():
        return WIKI_FALLBACK
    return CONTENT_WIKI


def _parse_frontmatter(path: pathlib.Path) -> tuple[dict[str, Any], str]:
    """Lightweight YAML frontmatter parser — avoids a hard dep on python-frontmatter."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    try:
        _, fm, body = text.split("---", 2)
    except ValueError:
        return {}, text
    try:
        import yaml  # type: ignore
        meta = yaml.safe_load(fm) or {}
    except ImportError:
        # Fallback: very-naive key:value parsing for top-level scalars only.
        meta = {}
        for line in fm.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip("'\"")
    return meta, body.strip()


def _report_to_item(meta: dict[str, Any], body: str, path: pathlib.Path) -> dict[str, Any]:
    """Project a report's frontmatter + body to the dashboard ITEM shape.

    Matches the inlined ITEMS array in apps/dashboard/index.html:
        { id, topic, industry, title, desc, author, source, published, url, mini_report: {topic_sentence, bullets} }
    plus the additional semantic fields from schemas/report.schema.json.
    """
    return {
        "id": meta.get("id") or path.stem,
        "topic": (meta.get("themes") or ["unknown"])[0] if isinstance(meta.get("themes"), list) else meta.get("themes", "unknown"),
        "industry": meta.get("industry", ""),
        "title": meta.get("title", path.stem),
        "desc": (meta.get("mini_report") or {}).get("topic_sentence", "") or meta.get("subtitle", ""),
        "author": meta.get("author", ""),
        "source": meta.get("source_publication", ""),
        "published": meta.get("published_at") or meta.get("date", ""),
        "url": meta.get("url", ""),
        "mini_report": meta.get("mini_report", {"topic_sentence": "", "bullets": []}),
        "report_path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
        # Semantic surface (ADR-009) — may be empty on day one
        "entities": meta.get("entities", []),
        "themes": meta.get("themes", []),
        "topics": meta.get("topics", []),
        "tags": meta.get("tags", []),
        "signal_score": meta.get("signal_score"),
        "novelty_score": meta.get("novelty_score"),
        "confidence": meta.get("confidence"),
        # Generation provenance
        "prompt_version": meta.get("prompt_version"),
        "model": meta.get("model"),
        "template_version": meta.get("template_version"),
        "generated_at": meta.get("generated_at"),
    }


def _soft_check(meta: dict[str, Any], path: pathlib.Path) -> list[str]:
    """Structural fallback when jsonschema is unavailable or schema can't load."""
    required = ["id", "type", "date", "title", "sources", "generated_at"]
    return [f"{path.name}: missing {k}" for k in required if k not in meta]


def _build_schema_store() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Load report.schema.json + all sibling schemas into a local store so
    jsonschema's RefResolver doesn't try to HTTP-fetch atlas.local URLs."""
    schema_path = SCHEMAS / "report.schema.json"
    if not schema_path.exists():
        return {}, {}
    root = json.loads(schema_path.read_text(encoding="utf-8"))
    store: dict[str, dict[str, Any]] = {}
    for sf in SCHEMAS.glob("*.schema.json"):
        try:
            s = json.loads(sf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(s, dict) and isinstance(s.get("$id"), str):
            store[s["$id"]] = s
    return root, store


def _validate(meta: dict[str, Any], path: pathlib.Path) -> list[str]:
    """Validate a report frontmatter against schemas/report.schema.json.

    Returns a list of error strings (empty if valid). Falls back to a soft
    structural check if jsonschema isn't installed or schema resolution fails.
    """
    try:
        import jsonschema  # type: ignore
        from jsonschema import RefResolver  # type: ignore
    except ImportError:
        return _soft_check(meta, path)

    schema, store = _build_schema_store()
    if not schema:
        return []

    try:
        resolver = RefResolver.from_schema(schema, store=store)
        validator_cls = jsonschema.validators.validator_for(schema)
        validator = validator_cls(schema, resolver=resolver)
        errors = list(validator.iter_errors(meta))
        return [f"{path.name}: {e.message}" for e in errors]
    except Exception as e:
        print(f"WARN: schema validation degraded for {path.name} ({type(e).__name__}: {e}); using soft check.", file=sys.stderr)
        return _soft_check(meta, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Only process reports with frontmatter date == YYYY-MM-DD")
    parser.add_argument("--validate-only", action="store_true", help="Validate but don't write outputs")
    args = parser.parse_args()

    reports_dir = _resolve_reports_dir()
    print(f"Reading reports from: {reports_dir.relative_to(REPO_ROOT)}", file=sys.stderr)

    items: list[dict[str, Any]] = []
    embeddings_queue: list[dict[str, Any]] = []
    errors: list[str] = []

    if not reports_dir.exists():
        print("WARNING: no reports directory found — emitting empty index.", file=sys.stderr)

    for md_path in sorted(reports_dir.rglob("*.md")) if reports_dir.exists() else []:
        meta, body = _parse_frontmatter(md_path)
        if args.date and meta.get("date") != args.date:
            continue
        errs = _validate(meta, md_path)
        if errs:
            errors.extend(errs)
            continue
        item = _report_to_item(meta, body, md_path)
        items.append(item)
        if not meta.get("embeddings_ref"):
            embeddings_queue.append({
                "report_id": item["id"],
                "report_path": item["report_path"],
                "queued_at": datetime.now(timezone.utc).isoformat(),
            })

    if errors:
        print(f"VALIDATION ERRORS ({len(errors)}):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        if args.validate_only:
            return 1

    if args.validate_only:
        print(f"OK — {len(items)} valid reports.", file=sys.stderr)
        return 0

    now = datetime.now(timezone.utc).isoformat()
    GENERATED.mkdir(parents=True, exist_ok=True)

    (GENERATED / "index.json").write_text(json.dumps({
        "generated_at": now,
        "schema_version": SCHEMA_VERSION,
        "items": items,
    }, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    (GENERATED / "search-index.json").write_text(json.dumps({
        "generated_at": now,
        "schema_version": SCHEMA_VERSION,
        "documents": [
            {
                "id": it["id"],
                "title": it["title"],
                "desc": it["desc"],
                "topic_sentence": (it.get("mini_report") or {}).get("topic_sentence", ""),
                "bullets": (it.get("mini_report") or {}).get("bullets", []),
                "themes": it.get("themes", []),
                "industry": it.get("industry", ""),
                "published": it["published"],
            }
            for it in items
        ],
    }, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    (GENERATED / "embeddings-ready.json").write_text(json.dumps({
        "generated_at": now,
        "schema_version": SCHEMA_VERSION,
        "queue": embeddings_queue,
    }, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print(f"Wrote {len(items)} items to generated/index.json", file=sys.stderr)
    print(f"Queued {len(embeddings_queue)} reports for embedding", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
