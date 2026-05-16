"""LangGraph node: PUBLISH — broadcast `news.created` to dashboard via Redis pub/sub."""

from __future__ import annotations

import json
import time

import redis.asyncio as redis_asyncio

from app.core.config import settings  # type: ignore[import-not-found]

from packages.automation.pipeline.state import PipelineState


async def run(state: PipelineState) -> PipelineState:
    t0 = time.perf_counter()
    client = redis_asyncio.from_url(settings.REDIS_URL, decode_responses=True)
    payload = {
        "type": "news.created",
        "payload": {
            "id": str(state.news_id),
            "thesis": state.summarized["thesis"],
            "bullets": state.summarized["bullets"],
            "region": state.classified["region"],
            "bucket": state.classified["bucket"],
            "industries": state.classified.get("industries", []),
            "entities": state.classified.get("entities", []),
            "raw_path": state.raw_path,
        },
    }
    await client.publish("events:global", json.dumps(payload))
    await client.aclose()
    state.record_step("publish", "done", latency_ms=int((time.perf_counter() - t0) * 1000))
    return state
