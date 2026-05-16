"""Report generation: institutional-grade daily brief.

Three sections per bucket:
  • Executive thesis (3 sentences max)
  • Key developments (bullet list, each with [src:N] citations)
  • Implications (analyst-voice, 2-3 paragraphs)
"""

from langchain_anthropic import ChatAnthropic

from agents.config import settings
from agents.db import items_for_date, save_report
from agents.prompts.registry import get_prompt

_llm = ChatAnthropic(
    model=settings.report_model,
    temperature=0.3,
    max_tokens=8000,
)


async def report_generation_agent(state: dict) -> dict:
    """Per-item runs are no-ops here; the batch daily-report path calls build_report."""
    return {"report_inclusion": None}


async def render_daily_report(date_str: str, report_type: str = "master") -> str:
    items = await items_for_date(date_str)
    if not items:
        return ""
    prompt = get_prompt("report_generation")
    rendered = prompt.format(
        date=date_str,
        type=report_type,
        items_json=_serialize_items(items),
    )
    resp = await _llm.ainvoke(rendered)
    body_md: str = resp.content if isinstance(resp.content, str) else str(resp.content)
    await save_report(
        date=date_str,
        type=report_type,
        body_md=body_md,
        model=settings.report_model,
        prompt_version=prompt.version,
    )
    return body_md


def _serialize_items(items: list) -> str:
    import json

    return json.dumps(
        [
            {
                "id": str(i.id),
                "title": i.title,
                "url": i.source_url,
                "thesis": i.summary.thesis if i.summary else None,
                "points": [p.get("text") for p in (i.summary.supporting_points if i.summary else [])],
                "bucket": i.classification.bucket.value if i.classification else None,
                "industries": i.classification.industries if i.classification else [],
            }
            for i in items
        ],
        ensure_ascii=False,
    )
