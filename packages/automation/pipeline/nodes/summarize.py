"""LangGraph node: SUMMARIZE — produce thesis + 3 bullets for dashboard display."""

from __future__ import annotations

import json
import time
from pathlib import Path

from packages.agents.models import get_chat

from packages.automation.pipeline.state import PipelineState

PROMPT = (Path(__file__).parents[2].parent / "agents" / "prompts" / "summarizer.txt").read_text(encoding="utf-8")


async def run(state: PipelineState) -> PipelineState:
    t0 = time.perf_counter()
    payload = {
        "extracted": state.extracted,
        "classified": state.classified,
        "body": state.content[:6000],
    }
    chat = get_chat("claude-sonnet-4-6")
    res = await chat.chat(system=PROMPT, user=json.dumps(payload, ensure_ascii=False), max_tokens=600, temperature=0.3)

    parsed = json.loads(res["text"])
    # Defensive shape check — summarizer must return thesis + exactly 3 bullets
    assert isinstance(parsed.get("thesis"), str)
    bullets = parsed.get("bullets") or []
    if len(bullets) != 3:
        # Pad / trim to 3
        bullets = (bullets + ["", "", ""])[:3]
    state.summarized = {"thesis": parsed["thesis"], "bullets": bullets}

    state.record_step(
        "summarize", "done",
        latency_ms=int((time.perf_counter() - t0) * 1000),
        tokens=res["tokens_in"] + res["tokens_out"],
        model="claude-sonnet-4-6",
    )
    return state
