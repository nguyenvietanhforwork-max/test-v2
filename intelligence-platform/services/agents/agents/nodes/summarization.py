"""Summarization: produce thesis + supporting points + implications + data points.

Spec rule: the first sentence is the topic sentence (thesis). Every supporting
point carries a citation offset back into the raw text for traceability.
"""

from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

from agents.config import settings
from agents.db import upsert_summary
from agents.prompts.registry import get_prompt


class Point(BaseModel):
    text: str
    citation_offsets: tuple[int, int] | None = None


class StructuredSummary(BaseModel):
    thesis: str
    supporting_points: list[Point]
    implications: list[Point]
    data_points: list[Point]


_llm = ChatAnthropic(
    model=settings.summarization_model,
    temperature=0.2,
    max_tokens=2048,
).with_structured_output(StructuredSummary)


async def summarization_agent(state: dict) -> dict:
    prompt = get_prompt("summarization")
    classification = state.get("classification") or {}
    result: StructuredSummary = await _llm.ainvoke(
        prompt.format(
            text=state["raw_text"][:12000],
            language=state.get("language", "vi"),
            bucket=classification.get("bucket", "unknown"),
            industries=", ".join(classification.get("industries", [])),
        )
    )
    await upsert_summary(
        news_item_id=state["news_item_id"],
        thesis=result.thesis,
        supporting_points=[p.model_dump() for p in result.supporting_points],
        implications=[p.model_dump() for p in result.implications],
        data_points=[p.model_dump() for p in result.data_points],
        model=settings.summarization_model,
        prompt_version=prompt.version,
    )
    return {"summary": result.model_dump()}
