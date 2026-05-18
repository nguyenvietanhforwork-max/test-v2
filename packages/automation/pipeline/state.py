"""Typed pipeline state — flows through every LangGraph node."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class PipelineState:
    # ---------- input ----------
    raw_path: str                            # path inside the vault
    content: str                             # raw markdown body
    content_hash: str                        # sha256 of normalized content
    job_id: str                              # UUID for this run

    # ---------- step outputs ----------
    extracted: dict[str, Any] = field(default_factory=dict)
    classified: dict[str, Any] = field(default_factory=dict)
    summarized: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None

    # ---------- persistence ----------
    news_id: UUID | None = None
    wiki_path: str | None = None

    # ---------- telemetry ----------
    step_history: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    total_tokens: int = 0

    # ---------- helpers ----------
    def record_step(
        self,
        name: str,
        status: str,
        *,
        latency_ms: int | None = None,
        tokens: int | None = None,
        model: str | None = None,
        error: str | None = None,
    ) -> None:
        self.step_history.append({
            "name": name, "status": status,
            "latency_ms": latency_ms, "tokens": tokens,
            "model": model, "error": error,
            "at": datetime.utcnow().isoformat(),
        })
        if tokens:
            self.total_tokens += tokens
        if error:
            self.errors.append(error)
