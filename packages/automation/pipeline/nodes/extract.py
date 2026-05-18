"""LangGraph node: EXTRACT — pull structured metadata from raw markdown."""

from __future__ import annotations

import json
import time
from pathlib import Path

import frontmatter

from packages.agents.models import get_chat

from packages.automation.pipeline.state import PipelineState

PROMPT_PATH = Path(__file__).parents[2].parent / "agents" / "prompts" / "extractor.txt"
PROMPT = PROMPT_PATH.read_text(encoding="utf-8")


async def run(state: PipelineState) -> PipelineState:
    t0 = time.perf_counter()
    fm = frontmatter.loads(state.content)
    user_msg = f"FRONTMATTER:\n{json.dumps(fm.metadata, ensure_ascii=False)}\n\nBODY:\n{fm.content[:8000]}"

    chat = get_chat("claude-sonnet-4-6")
    res = await chat.chat(system=PROMPT, user=user_msg, max_tokens=1200, temperature=0.1)

    try:
        state.extracted = json.loads(res["text"])
    except json.JSONDecodeError:
        # Try one re-prompt with stricter wording
        retry_user = user_msg + "\n\nPRIOR RESPONSE FAILED JSON VALIDATION. RETURN PURE JSON."
        res = await chat.chat(system=PROMPT, user=retry_user, max_tokens=1200, temperature=0)
        state.extracted = json.loads(res["text"])

    # Merge frontmatter as a fallback for fields the LLM missed.
    state.extracted.setdefault("url", fm.metadata.get("url"))
    state.extracted.setdefault("source", fm.metadata.get("source") or "Unknown")
    state.extracted.setdefault("published_at", fm.metadata.get("published") or fm.metadata.get("date"))

    state.record_step(
        "extract", "done",
        latency_ms=int((time.perf_counter() - t0) * 1000),
        tokens=res["tokens_in"] + res["tokens_out"],
        model="claude-sonnet-4-6",
    )
    return state
