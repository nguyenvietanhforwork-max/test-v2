"""LangGraph state machine wiring the seven agents together."""

from typing import Optional, TypedDict

from langgraph.graph import END, StateGraph

from agents.nodes import (
    classification_agent,
    dashboard_sync_agent,
    ingestion_agent,
    pdf_generation_agent,
    report_generation_agent,
    summarization_agent,
    wiki_enrichment_agent,
)


class PipelineState(TypedDict, total=False):
    news_item_id: str
    raw_text: str
    language: str
    classification: Optional[dict]
    summary: Optional[dict]
    entities: list[dict]
    wiki_updates: list[dict]
    report_inclusion: Optional[dict]
    pdf_url: Optional[str]
    errors: list[str]
    # batching control
    skip_report: bool


def route_after_wiki(state: PipelineState) -> str:
    """Single-item runs skip the report step; the report agent is invoked
    by the scheduled `daily-report` workflow, not per-item."""
    if state.get("skip_report", True):
        return "sync"
    return "report"


def build_graph():
    g = StateGraph(PipelineState)
    g.add_node("ingestion", ingestion_agent)
    g.add_node("classification", classification_agent)
    g.add_node("summarization", summarization_agent)
    g.add_node("wiki_enrichment", wiki_enrichment_agent)
    g.add_node("report", report_generation_agent)
    g.add_node("pdf", pdf_generation_agent)
    g.add_node("sync", dashboard_sync_agent)

    g.set_entry_point("ingestion")
    g.add_edge("ingestion", "classification")
    g.add_edge("classification", "summarization")
    g.add_edge("summarization", "wiki_enrichment")
    g.add_conditional_edges("wiki_enrichment", route_after_wiki, {"sync": "sync", "report": "report"})
    g.add_edge("report", "pdf")
    g.add_edge("pdf", "sync")
    g.add_edge("sync", END)
    return g.compile()
