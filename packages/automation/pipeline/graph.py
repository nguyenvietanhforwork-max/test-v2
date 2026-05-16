"""LangGraph state machine for the ingest pipeline.

       ┌─ extract ─┐
START ─┤           ├─ classify ─ summarize ─ embed ─ persist ─ publish ─ END
       └  quarantine  (on bad frontmatter)
"""

from __future__ import annotations

import json
from datetime import datetime

from langgraph.graph import END, START, StateGraph

from packages.automation.pipeline.nodes import classify, embed, extract, persist, publish, summarize
from packages.automation.pipeline.state import PipelineState


def _gate_after_extract(state: PipelineState) -> str:
    """If the extractor failed to recover a title, send to quarantine."""
    if not state.extracted.get("title"):
        return "quarantine"
    return "classify"


async def quarantine(state: PipelineState) -> PipelineState:
    state.errors.append("missing title — quarantined")
    state.record_step("quarantine", "done")
    state.ended_at = datetime.utcnow()
    return state


def build() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("extract", extract.run)
    graph.add_node("classify", classify.run)
    graph.add_node("summarize", summarize.run)
    graph.add_node("embed", embed.run)
    graph.add_node("persist", persist.run)
    graph.add_node("publish", publish.run)
    graph.add_node("quarantine", quarantine)

    graph.add_edge(START, "extract")
    graph.add_conditional_edges("extract", _gate_after_extract, {"classify": "classify", "quarantine": "quarantine"})
    graph.add_edge("classify", "summarize")
    graph.add_edge("summarize", "embed")
    graph.add_edge("embed", "persist")
    graph.add_edge("persist", "publish")
    graph.add_edge("publish", END)
    graph.add_edge("quarantine", END)

    return graph.compile()


PIPELINE = build()


async def run_pipeline(initial: PipelineState) -> PipelineState:
    initial.started_at = datetime.utcnow()
    final: PipelineState = await PIPELINE.ainvoke(initial)
    final.ended_at = datetime.utcnow()
    return final


if __name__ == "__main__":
    # Smoke test
    print(json.dumps([n for n in PIPELINE.nodes], indent=2))
