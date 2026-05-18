"""/feedback endpoint — human preference intelligence ingest.

Per ADR-007, feedback is canonical intelligence. The canonical store is
feedback/ratings.json on disk (file-first, per ADR-006). The DB layer is
optional and derived.

Two acceptable payload shapes:

  1. Single rating record (matches schemas/rating.schema.json)
  2. Dashboard preferences export (matches the v2 dashboard's exportPreferences()
     output — contains raw_ratings[])

The endpoint detects which it is and normalizes both to individual rating
records in feedback/ratings.json. Idempotent against (rated_at, report_id).
"""

from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()

# Resolve repo root relative to this file: apps/api/app/api/v1/feedback.py → repo root is 5 parents up.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
RATINGS_FILE = REPO_ROOT / "feedback" / "ratings.json"


class Criteria(BaseModel):
    data_density: int | None = Field(default=None, ge=1, le=5)
    insight_quality: int | None = Field(default=None, ge=1, le=5)
    writing_style: int | None = Field(default=None, ge=1, le=5)


class RatingRecord(BaseModel):
    """Single rating record. Mirrors schemas/rating.schema.json."""
    rated_at: str | None = None
    report_id: str
    criteria: Criteria
    length_appropriateness: str | None = None
    tags: list[str] = []
    notes: str = ""
    prompt_version: str | None = None
    model: str | None = None
    template_version: str | None = None
    rater: str | None = None
    client: str = "dashboard-api-push"


class PreferencesPayload(BaseModel):
    """Dashboard exportPreferences() shape — the v2 dashboard's bulk export."""
    exported_at: str | None = None
    n_rated: int | None = None
    averages: dict[str, float] | None = None
    raw_ratings: list[dict[str, Any]] = []


def _load_ratings() -> dict[str, Any]:
    if not RATINGS_FILE.exists():
        return {"schema_version": 1, "schema_ref": "schemas/rating.schema.json", "ratings": []}
    return json.loads(RATINGS_FILE.read_text(encoding="utf-8"))


def _save_ratings(data: dict[str, Any]) -> None:
    RATINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RATINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_dashboard_raw(raw: dict[str, Any], exported_at: str) -> dict[str, Any]:
    """Translate the dashboard's per-item rating into the canonical RatingRecord shape."""
    criteria = raw.get("criteria") or {}
    return {
        "rated_at": raw.get("rated_at") or exported_at,
        "report_id": raw.get("report_id") or raw.get("id", ""),
        "criteria": {
            "data_density": criteria.get("data") or raw.get("data_density"),
            "insight_quality": criteria.get("insight") or raw.get("insight_quality"),
            "writing_style": criteria.get("style") or raw.get("writing_style"),
        },
        "length_appropriateness": raw.get("length") or raw.get("length_appropriateness"),
        "tags": raw.get("tags", []),
        "notes": raw.get("notes", ""),
        "prompt_version": raw.get("prompt_version"),
        "model": raw.get("model"),
        "template_version": raw.get("template_version"),
        "client": "dashboard-api-push",
    }


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def submit_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Accept either a single rating record or a dashboard preferences export.

    Returns:
        { "added": int, "skipped_duplicates": int, "total_ratings_now": int }
    """
    data = _load_ratings()
    seen = {(r.get("rated_at"), r.get("report_id")) for r in data["ratings"]}
    added = 0
    skipped = 0

    # Detect shape
    if "raw_ratings" in payload:
        # Dashboard bulk export
        exported_at = payload.get("exported_at") or datetime.now(timezone.utc).isoformat()
        for raw in payload.get("raw_ratings", []):
            record = _normalize_dashboard_raw(raw, exported_at)
            key = (record["rated_at"], record["report_id"])
            if key in seen:
                skipped += 1
                continue
            data["ratings"].append(record)
            seen.add(key)
            added += 1
    elif "report_id" in payload and "criteria" in payload:
        # Single rating record
        try:
            record = RatingRecord(**payload).model_dump()
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Invalid rating shape: {e}") from e
        if not record.get("rated_at"):
            record["rated_at"] = datetime.now(timezone.utc).isoformat()
        key = (record["rated_at"], record["report_id"])
        if key in seen:
            skipped = 1
        else:
            data["ratings"].append(record)
            added = 1
    else:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Payload must be either a single rating (with report_id + criteria) or a dashboard preferences export (with raw_ratings)."
        )

    _save_ratings(data)
    return {
        "added": added,
        "skipped_duplicates": skipped,
        "total_ratings_now": len(data["ratings"]),
        "stored_at": str(RATINGS_FILE.relative_to(REPO_ROOT)).replace("\\", "/"),
    }


@router.get("/summary")
async def feedback_summary() -> dict[str, Any]:
    """Lightweight summary for the dashboard's stats panel."""
    data = _load_ratings()
    ratings = data.get("ratings", [])
    if not ratings:
        return {"n_ratings": 0, "averages": {}}

    sums = {"data_density": 0.0, "insight_quality": 0.0, "writing_style": 0.0}
    counts = {"data_density": 0, "insight_quality": 0, "writing_style": 0}
    for r in ratings:
        crit = r.get("criteria") or {}
        for k in sums:
            v = crit.get(k)
            if v is not None:
                sums[k] += v
                counts[k] += 1
    avgs = {k: (sums[k] / counts[k]) for k in sums if counts[k]}
    return {"n_ratings": len(ratings), "averages": avgs}
