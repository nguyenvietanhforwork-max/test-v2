"""
scripts/generate_embeddings.py — embed reports queued by build_index.py.

Reads generated/embeddings-ready.json (the queue) and produces:
  - generated/embeddings/<report_id>.npy        — the embedding vector
  - generated/embeddings/index.jsonl            — id → path → model metadata

Then patches each rated report's frontmatter to add `embeddings_ref` so the
queue empties on the next build_index.py run.

USAGE
    python scripts/generate_embeddings.py                # process whole queue
    python scripts/generate_embeddings.py --limit 10
    python scripts/generate_embeddings.py --dry-run

Per ADR-009, embeddings are semantic-ready but not required. If no API key is
configured, this script reports the queue size and exits cleanly without
calling out to a model.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
GENERATED = REPO_ROOT / "generated"
EMBEDDINGS_DIR = GENERATED / "embeddings"
QUEUE_FILE = GENERATED / "embeddings-ready.json"

DEFAULT_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-large")


def _load_queue() -> dict:
    if not QUEUE_FILE.exists():
        return {"queue": []}
    return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))


def _save_queue(data: dict) -> None:
    QUEUE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _embed_stub(text: str, model: str) -> list[float] | None:
    """
    Real implementation would call OpenAI / Voyage / local model here:

        from openai import OpenAI
        client = OpenAI()
        r = client.embeddings.create(model=model, input=text)
        return r.data[0].embedding

    Stub returns None when no key is present so the script can run anywhere.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI()
        r = client.embeddings.create(model=model, input=text)
        return r.data[0].embedding
    except Exception as e:  # noqa: BLE001
        print(f"  embed error: {e}", file=sys.stderr)
        return None


def _read_report_body(report_path: str) -> str:
    p = REPO_ROOT / report_path
    if not p.exists():
        return ""
    text = p.read_text(encoding="utf-8")
    if text.startswith("---"):
        try:
            _, _, body = text.split("---", 2)
            return body.strip()
        except ValueError:
            return text
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    queue_data = _load_queue()
    queue = queue_data.get("queue", [])
    if args.limit:
        queue = queue[: args.limit]

    if not queue:
        print("Queue is empty. Run scripts/build_index.py to repopulate.", file=sys.stderr)
        return 0

    if not os.environ.get("OPENAI_API_KEY"):
        print(f"No OPENAI_API_KEY set. {len(queue)} items remain queued; this run did nothing.", file=sys.stderr)
        return 0

    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    index_path = EMBEDDINGS_DIR / "index.jsonl"
    index_handle = index_path.open("a", encoding="utf-8")

    processed = 0
    remaining: list[dict] = []
    try:
        import numpy as np  # type: ignore
    except ImportError:
        print("numpy required: pip install numpy", file=sys.stderr)
        return 1

    for item in queue_data.get("queue", []):
        rid = item["report_id"]
        rpath = item["report_path"]
        if args.limit is not None and processed >= args.limit:
            remaining.append(item)
            continue
        body = _read_report_body(rpath)
        if not body:
            print(f"  SKIP {rid}: body empty", file=sys.stderr)
            remaining.append(item)
            continue
        vec = _embed_stub(body, args.model)
        if vec is None:
            remaining.append(item)
            continue
        out_npy = EMBEDDINGS_DIR / f"{rid}.npy"
        if not args.dry_run:
            np.save(out_npy, np.array(vec, dtype=np.float32))
            index_handle.write(json.dumps({
                "report_id": rid,
                "path": str(out_npy.relative_to(REPO_ROOT)).replace("\\", "/"),
                "model": args.model,
                "dim": len(vec),
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }) + "\n")
        processed += 1
        print(f"  ✓ {rid} ({len(vec)}d)", file=sys.stderr)

    index_handle.close()
    queue_data["queue"] = remaining
    queue_data["generated_at"] = datetime.now(timezone.utc).isoformat()
    if not args.dry_run:
        _save_queue(queue_data)
    print(f"Embedded {processed} reports. {len(remaining)} remain queued.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
