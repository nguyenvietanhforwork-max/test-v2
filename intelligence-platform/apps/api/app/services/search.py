"""Hybrid search service. pgvector cosine + Meilisearch lexical, RRF re-ranked."""

from typing import Any

import httpx
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.news import SearchHit

log = structlog.get_logger()


async def hybrid_search(
    session: AsyncSession, q: str, filters: dict, k: int
) -> list[SearchHit]:
    vec_hits = await _vector_search(session, q, k)
    lex_hits = await _meilisearch(q, k) if settings.meilisearch_host else []
    return _rrf_merge(vec_hits, lex_hits, k)


async def _vector_search(session: AsyncSession, q: str, k: int) -> list[dict[str, Any]]:
    """Embed q and run pgvector cosine."""
    from app.services.embeddings import embed_text

    vec = await embed_text(q)
    rows = await session.execute(
        text(
            """
            select e.owner_id::text as news_item_id,
                   n.title as title,
                   left(n.raw_text, 280) as snippet,
                   n.publish_date as publish_date,
                   1 - (e.vector <=> :q) as score
              from embeddings e
              join news_items n on n.id = e.owner_id
             where e.owner_table = 'news_items'
             order by e.vector <=> :q
             limit :k
            """
        ),
        {"q": vec, "k": k},
    )
    return [dict(r._mapping) for r in rows]


async def _meilisearch(q: str, k: int) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=2) as client:
        try:
            resp = await client.post(
                f"{settings.meilisearch_host}/indexes/news/search",
                json={"q": q, "limit": k},
                headers={"Authorization": f"Bearer {settings.meilisearch_master_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                {
                    "news_item_id": h["id"],
                    "title": h["title"],
                    "snippet": h.get("snippet", ""),
                    "publish_date": h.get("publish_date"),
                    "score": h.get("_rankingScore", 0.5),
                }
                for h in data.get("hits", [])
            ]
        except httpx.HTTPError as e:
            log.warning("meili.error", error=str(e))
            return []


def _rrf_merge(
    a: list[dict], b: list[dict], k: int, kappa: int = 60
) -> list[SearchHit]:
    """Reciprocal Rank Fusion."""
    scores: dict[str, dict] = {}
    for rank, hit in enumerate(a):
        scores[hit["news_item_id"]] = {**hit, "score": 1 / (kappa + rank + 1)}
    for rank, hit in enumerate(b):
        if hit["news_item_id"] in scores:
            scores[hit["news_item_id"]]["score"] += 1 / (kappa + rank + 1)
        else:
            scores[hit["news_item_id"]] = {**hit, "score": 1 / (kappa + rank + 1)}
    merged = sorted(scores.values(), key=lambda x: x["score"], reverse=True)[:k]
    return [SearchHit.model_validate(m) for m in merged]
