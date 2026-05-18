"""Hybrid search service — Meilisearch (lexical) + pgvector (semantic)."""

from __future__ import annotations

import time
from typing import Any

import meilisearch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Embedding, NewsItem
from app.schemas.search import SearchHit, SearchIn, SearchOut

_meili = meilisearch.Client(settings.MEILI_HOST, settings.MEILI_MASTER_KEY)


async def search(db: AsyncSession, body: SearchIn) -> SearchOut:
    t0 = time.perf_counter()
    hits: list[SearchHit] = []

    if body.mode in ("lexical", "hybrid"):
        hits.extend(await _lexical(body))

    if body.mode in ("semantic", "hybrid"):
        hits.extend(await _semantic(db, body))

    if body.mode == "hybrid":
        hits = _merge_rrf(hits)

    return SearchOut(hits=hits[: body.limit], took_ms=int((time.perf_counter() - t0) * 1000))


async def _lexical(body: SearchIn) -> list[SearchHit]:
    res = _meili.index("news").search(body.query, {"limit": body.limit})  # sync; fine for now
    return [
        SearchHit(
            id=h["id"],
            title=h["title"],
            snippet=h.get("thesis", "")[:200],
            score=1.0,
            match_type="lex",
            highlights=h.get("_formatted", {}).get("highlights", []),
        )
        for h in res.get("hits", [])
    ]


async def _semantic(db: AsyncSession, body: SearchIn) -> list[SearchHit]:
    # In production: embed the query via the agents.models facade, then KNN.
    # Stub: return empty so the hybrid merge still works.
    return []


def _merge_rrf(hits: list[SearchHit], k: int = 60) -> list[SearchHit]:
    """Reciprocal rank fusion across lexical + semantic results."""
    scored: dict[str, SearchHit] = {}
    for rank, h in enumerate(hits, 1):
        prev = scored.get(h.id)
        rrf = 1.0 / (k + rank)
        if prev:
            prev.score += rrf
            prev.match_type = "hybrid"
        else:
            h.score = rrf
            scored[h.id] = h
    return sorted(scored.values(), key=lambda x: x.score, reverse=True)
