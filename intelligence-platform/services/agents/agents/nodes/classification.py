"""Classification: bucket + industries + countries + companies via Haiku.

Uses structured output (function-calling). Deterministic temperature.
"""

import json

from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

from agents.config import settings
from agents.db import upsert_classification
from agents.prompts.registry import get_prompt


class ClassificationOut(BaseModel):
    bucket: str  # vn_corp | intl_corp | vn_macro | intl_macro
    industries: list[str]
    countries: list[str]
    companies: list[str]
    confidence: float


_llm = ChatAnthropic(
    model=settings.classification_model,
    temperature=0,
    max_tokens=1024,
).with_structured_output(ClassificationOut)


async def classification_agent(state: dict) -> dict:
    prompt = get_prompt("classification")  # versioned
    raw = state["raw_text"]
    result: ClassificationOut = await _llm.ainvoke(prompt.format(text=raw[:8000]))

    await upsert_classification(
        news_item_id=state["news_item_id"],
        bucket=result.bucket,
        industries=result.industries,
        countries=result.countries,
        companies=result.companies,
        confidence=result.confidence,
        model=settings.classification_model,
        prompt_version=prompt.version,
    )
    return {"classification": result.model_dump()}
