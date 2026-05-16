"""LangGraph node: EMBED — vector representation for semantic search + graph."""

from __future__ import annotations

import time

from packages.agents.models import get_embeddings

from packages.automation.pipeline.state import PipelineState


async def run(state: PipelineState) -> PipelineState:
    t0 = time.perf_counter()
    # Embed: thesis + bullets concatenated. Keeps recall high without bloating token spend.
    text = state.summarized["thesis"] + "\n" + "\n".join(state.summarized["bullets"])
    emb = await get_embeddings().embed([text])
    state.embedding = emb[0]

    state.record_step(
        "embed", "done",
        latency_ms=int((time.perf_counter() - t0) * 1000),
        tokens=len(text.split()),  # rough proxy
        model="text-embedding-3-large",
    )
    return state
