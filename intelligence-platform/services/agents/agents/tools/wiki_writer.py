"""Wiki write tool — wraps the LLM call inside the wiki_enrichment node."""

from langchain_anthropic import ChatAnthropic

from agents.config import settings

_llm = ChatAnthropic(model=settings.summarization_model, temperature=0.2, max_tokens=4096)


async def draft_wiki_update(
    *, entity: str, existing_context: list[str], new_summary: dict, prompt
) -> str:
    rendered = prompt.format(
        entity=entity,
        entity_title=entity,
        existing="\n\n---\n\n".join(existing_context) if existing_context else "(none)",
        new_summary=new_summary.get("thesis", ""),
    )
    resp = await _llm.ainvoke(rendered)
    content = resp.content if isinstance(resp.content, str) else str(resp.content)
    return content.strip()
