"""Wiki enrichment: maintain company/industry/concept pages.

For each named entity in the classification, this agent:
1. retrieves existing wiki content via pgvector
2. asks Sonnet to *merge*, not duplicate
3. upserts the result into wiki_pages
4. links wiki_page → news_item in wiki_page_sources
"""

import structlog

from agents.db import (
    list_entities_for_news_item,
    retrieve_wiki_context,
    upsert_wiki_page,
    link_wiki_to_news,
)
from agents.prompts.registry import get_prompt
from agents.tools.wiki_writer import draft_wiki_update

log = structlog.get_logger()


async def wiki_enrichment_agent(state: dict) -> dict:
    classification = state.get("classification") or {}
    entities = classification.get("companies", []) + classification.get("industries", [])

    updates: list[dict] = []
    for entity in entities[:8]:  # cap per news item for cost control
        try:
            context = await retrieve_wiki_context(entity, k=5)
            prompt = get_prompt("wiki_enrichment")
            new_body = await draft_wiki_update(
                entity=entity,
                existing_context=context,
                new_summary=state.get("summary", {}),
                prompt=prompt,
            )
            slug = _slugify(entity)
            await upsert_wiki_page(slug=slug, title=entity, body_md=new_body)
            await link_wiki_to_news(slug=slug, news_item_id=state["news_item_id"])
            updates.append({"slug": slug, "title": entity})
        except Exception as e:
            log.exception("wiki.enrich_failed", entity=entity, error=str(e))

    return {"wiki_updates": updates}


def _slugify(s: str) -> str:
    import re
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s
