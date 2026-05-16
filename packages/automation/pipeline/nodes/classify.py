"""LangGraph node: CLASSIFY — region / bucket / industries / entities / sentiment."""

from __future__ import annotations

import json
import time
from pathlib import Path

from packages.agents.models import get_chat

from packages.automation.pipeline.state import PipelineState

PROMPT = (Path(__file__).parents[2].parent / "agents" / "prompts" / "classifier.txt").read_text(encoding="utf-8")


async def run(state: PipelineState) -> PipelineState:
    t0 = time.perf_counter()
    payload = {
        "extracted": state.extracted,
        "body_snippet": state.content[:4000],
    }
    chat = get_chat("claude-sonnet-4-6")
    res = await chat.chat(system=PROMPT, user=json.dumps(payload, ensure_ascii=False), max_tokens=900, temperature=0.1)
    state.classified = json.loads(res["text"])

    state.record_step(
        "classify", "done",
        latency_ms=int((time.perf_counter() - t0) * 1000),
        tokens=res["tokens_in"] + res["tokens_out"],
        model="claude-sonnet-4-6",
    )
    return state
