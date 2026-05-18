"""
scripts/analyze_feedback.py — feedback intelligence aggregation.

Reads feedback/inbox/preferences-*.json (the dashboard's local export),
appends individual rating records to feedback/ratings.json, then aggregates:

  - feedback/analytics/per-prompt-version.json
  - feedback/analytics/per-model.json
  - feedback/analytics/per-template.json
  - feedback/datasets/preference-pairs.jsonl  (DPO-ready pairs)

Per ADR-007, every rating record is traceable to the prompt_version + model
+ template_version that produced the rated content.

USAGE
    python scripts/analyze_feedback.py                # full pass
    python scripts/analyze_feedback.py --since 2026-05-01
    python scripts/analyze_feedback.py --no-ingest    # only re-aggregate from ratings.json
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
FEEDBACK = REPO_ROOT / "feedback"
INBOX = FEEDBACK / "inbox"
RATINGS_FILE = FEEDBACK / "ratings.json"
ANALYTICS = FEEDBACK / "analytics"
DATASETS = FEEDBACK / "datasets"


def _load_ratings() -> dict[str, Any]:
    if not RATINGS_FILE.exists():
        return {"schema_version": 1, "schema_ref": "schemas/rating.schema.json", "ratings": []}
    return json.loads(RATINGS_FILE.read_text(encoding="utf-8"))


def _save_ratings(data: dict[str, Any]) -> None:
    RATINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RATINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _ingest_inbox() -> int:
    """Convert each preferences-*.json in inbox/ into rating records."""
    if not INBOX.exists():
        return 0
    data = _load_ratings()
    seen_keys = {(r.get("rated_at"), r.get("report_id")) for r in data["ratings"]}
    added = 0
    for f in sorted(INBOX.glob("preferences-*.json")):
        try:
            payload = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  SKIP {f.name}: invalid JSON ({e})", file=sys.stderr)
            continue

        # The dashboard's exportPreferences() shape:
        #   { exported_at, n_rated, averages, length_distribution, preferred_length,
        #     top_tags, style_profile_for_ai, instructions_for_next_generation,
        #     raw_ratings: [ { report_id, criteria: {data, insight, style},
        #                      length, tags: [...], notes, rated_at } ] }
        exported_at = payload.get("exported_at") or datetime.now(timezone.utc).isoformat()
        for raw in (payload.get("raw_ratings") or []):
            record = {
                "rated_at": raw.get("rated_at", exported_at),
                "report_id": raw.get("report_id") or raw.get("id", ""),
                "criteria": {
                    "data_density": raw.get("criteria", {}).get("data") or raw.get("data_density"),
                    "insight_quality": raw.get("criteria", {}).get("insight") or raw.get("insight_quality"),
                    "writing_style": raw.get("criteria", {}).get("style") or raw.get("writing_style"),
                },
                "length_appropriateness": raw.get("length") or raw.get("length_appropriateness"),
                "tags": raw.get("tags", []),
                "notes": raw.get("notes", ""),
                "prompt_version": raw.get("prompt_version"),
                "model": raw.get("model"),
                "template_version": raw.get("template_version"),
                "client": "dashboard-local-export",
            }
            # Drop None criteria so the schema validator doesn't choke
            record["criteria"] = {k: v for k, v in record["criteria"].items() if v is not None}
            key = (record["rated_at"], record["report_id"])
            if key in seen_keys:
                continue
            data["ratings"].append(record)
            seen_keys.add(key)
            added += 1
        # Move processed file to a sibling 'processed/' directory so we don't re-ingest
        processed_dir = INBOX / "processed"
        processed_dir.mkdir(exist_ok=True)
        try:
            f.rename(processed_dir / f.name)
        except OSError:
            pass

    _save_ratings(data)
    return added


def _aggregate(data: dict[str, Any], group_by: str) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in data["ratings"]:
        key = r.get(group_by) or "(unknown)"
        buckets[key].append(r)

    out: dict[str, Any] = {}
    for key, ratings in buckets.items():
        criteria_sums: dict[str, float] = defaultdict(float)
        criteria_counts: dict[str, int] = defaultdict(int)
        tag_counts: dict[str, int] = defaultdict(int)
        length_counts: dict[str, int] = defaultdict(int)
        for r in ratings:
            for c, v in (r.get("criteria") or {}).items():
                if v is None:
                    continue
                criteria_sums[c] += v
                criteria_counts[c] += 1
            for t in (r.get("tags") or []):
                tag_counts[t] += 1
            la = r.get("length_appropriateness")
            if la:
                length_counts[la] += 1
        out[key] = {
            "n_ratings": len(ratings),
            "averages": {c: criteria_sums[c] / criteria_counts[c] for c in criteria_sums if criteria_counts[c]},
            "top_tags": sorted(tag_counts.items(), key=lambda kv: -kv[1])[:10],
            "length_distribution": dict(length_counts),
        }
    return out


def _write_preference_pairs(data: dict[str, Any]) -> int:
    """Implicit DPO pairs: for each (theme, day), pair the highest-scoring report with the lowest."""
    by_bucket: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in data["ratings"]:
        crit = r.get("criteria") or {}
        score = sum(v for v in crit.values() if v) / max(1, len(crit))
        bucket = f"{(r.get('rated_at') or '')[:10]}"
        by_bucket[bucket].append({"rating": r, "score": score})

    pairs: list[dict[str, Any]] = []
    for bucket, rs in by_bucket.items():
        if len(rs) < 2:
            continue
        rs.sort(key=lambda x: x["score"])
        lowest, highest = rs[0], rs[-1]
        if highest["score"] - lowest["score"] < 1.0:
            continue
        pairs.append({
            "bucket": bucket,
            "chosen_report_id": highest["rating"]["report_id"],
            "chosen_score": highest["score"],
            "chosen_prompt_version": highest["rating"].get("prompt_version"),
            "rejected_report_id": lowest["rating"]["report_id"],
            "rejected_score": lowest["score"],
            "rejected_prompt_version": lowest["rating"].get("prompt_version"),
        })

    DATASETS.mkdir(parents=True, exist_ok=True)
    out = DATASETS / "preference-pairs.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for p in pairs:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    return len(pairs)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-ingest", action="store_true", help="Skip inbox ingestion; only re-aggregate")
    parser.add_argument("--since", help="Only include ratings rated_at >= this date (YYYY-MM-DD)")
    args = parser.parse_args()

    added = 0 if args.no_ingest else _ingest_inbox()
    print(f"Ingested {added} new ratings from feedback/inbox/", file=sys.stderr)

    data = _load_ratings()
    if args.since:
        data = {**data, "ratings": [r for r in data["ratings"] if (r.get("rated_at") or "") >= args.since]}

    ANALYTICS.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()

    for group in ("prompt_version", "model", "template_version"):
        agg = _aggregate(data, group)
        (ANALYTICS / f"per-{group.replace('_', '-')}.json").write_text(
            json.dumps({"generated_at": now, "group_by": group, "buckets": agg}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  wrote feedback/analytics/per-{group.replace('_', '-')}.json ({len(agg)} buckets)", file=sys.stderr)

    pairs = _write_preference_pairs(data)
    print(f"  wrote feedback/datasets/preference-pairs.jsonl ({pairs} pairs)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
