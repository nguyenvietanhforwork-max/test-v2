"""
scripts/build_graph.py — entity / theme graph builder.

Walks content/reports/**/*.md and content/wiki/entities/**/*.md frontmatter
to construct a graph of:

  - Entity nodes (from report.entities[])
  - Theme nodes (from report.themes[])
  - Report nodes (each report itself)
  - Edges: report → entity (mentions), report → theme (about), entity → entity (co-mentioned), report → report (related_reports)

Writes generated/graph.json conforming to a simple Cytoscape-compatible shape.

USAGE
    python scripts/build_graph.py [--validate-only]

Per ADR-009, this script populates the graph from frontmatter that the
pipeline already emits — no separate extraction step. If the entity / theme
data isn't yet populated, the graph is empty but valid.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT_REPORTS = REPO_ROOT / "content" / "reports"
CONTENT_WIKI = REPO_ROOT / "content" / "wiki"
WIKI_FALLBACK = REPO_ROOT / "wiki"
REPORTS_FALLBACK = REPO_ROOT / "Processed"
GENERATED = REPO_ROOT / "generated"


def _frontmatter(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    try:
        _, fm, _ = text.split("---", 2)
    except ValueError:
        return {}
    try:
        import yaml  # type: ignore
        return yaml.safe_load(fm) or {}
    except ImportError:
        return {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    reports_dir = CONTENT_REPORTS if CONTENT_REPORTS.exists() else REPORTS_FALLBACK

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    entity_keys: set[str] = set()
    theme_keys: set[str] = set()
    entity_cooccurrence: dict[tuple[str, str], int] = defaultdict(int)

    if reports_dir.exists():
        for md in sorted(reports_dir.rglob("*.md")):
            meta = _frontmatter(md)
            if not meta:
                continue
            report_id = meta.get("id") or md.stem
            nodes.append({
                "data": {
                    "id": report_id,
                    "label": meta.get("title", md.stem),
                    "type": "report",
                    "date": meta.get("date"),
                    "signal_score": meta.get("signal_score"),
                    "novelty_score": meta.get("novelty_score"),
                }
            })
            entities_in_report = []
            for ent in (meta.get("entities") or []):
                ent_id = f"entity:{ent.get('name')}"
                if ent_id not in entity_keys:
                    entity_keys.add(ent_id)
                    nodes.append({"data": {"id": ent_id, "label": ent.get("name"), "type": "entity", "entity_type": ent.get("type")}})
                edges.append({"data": {"id": f"{report_id}->{ent_id}", "source": report_id, "target": ent_id, "type": "mentions"}})
                entities_in_report.append(ent_id)
            # Co-occurrence edges among entities in same report
            for i, a in enumerate(entities_in_report):
                for b in entities_in_report[i + 1:]:
                    key = tuple(sorted((a, b)))
                    entity_cooccurrence[key] += 1
            for theme in (meta.get("themes") or []):
                th_id = f"theme:{theme}"
                if th_id not in theme_keys:
                    theme_keys.add(th_id)
                    nodes.append({"data": {"id": th_id, "label": theme, "type": "theme"}})
                edges.append({"data": {"id": f"{report_id}->{th_id}", "source": report_id, "target": th_id, "type": "about"}})
            for rel in (meta.get("related_reports") or []):
                rid = rel.get("report_id") if isinstance(rel, dict) else rel
                if rid:
                    edges.append({"data": {"source": report_id, "target": rid, "type": rel.get("relation", "see-also") if isinstance(rel, dict) else "see-also"}})

    # Co-occurrence edges
    for (a, b), weight in entity_cooccurrence.items():
        if weight < 2:
            continue
        edges.append({"data": {"id": f"coocc:{a}-{b}", "source": a, "target": b, "type": "co-mentioned", "weight": weight}})

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": 1,
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "reports": sum(1 for n in nodes if n["data"]["type"] == "report"),
            "entities": len(entity_keys),
            "themes": len(theme_keys),
            "edges": len(edges),
        },
    }

    if args.validate_only:
        print(f"OK — {out['stats']}", file=sys.stderr)
        return 0

    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "graph.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote generated/graph.json — {out['stats']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
