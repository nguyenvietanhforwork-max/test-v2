"""LangGraph node: PERSIST — write news_item, news_industries, news_entities, embedding.

Idempotent on content_hash (UNIQUE) — re-runs are safe.
"""

from __future__ import annotations

import time
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.models import Embedding, Entity, Industry, NewsEntity, NewsIndustry, NewsItem  # type: ignore[import-not-found]
from app.db.session import async_session  # type: ignore[import-not-found]

from packages.automation.pipeline.state import PipelineState


async def run(state: PipelineState) -> PipelineState:
    t0 = time.perf_counter()
    async with async_session() as db:
        # Find or insert by content_hash
        existing = (await db.execute(select(NewsItem).where(NewsItem.content_hash == state.content_hash))).scalar_one_or_none()
        if existing:
            state.news_id = existing.id
            state.record_step("persist", "done", latency_ms=int((time.perf_counter() - t0) * 1000))
            return state

        c = state.classified
        x = state.extracted
        s = state.summarized

        news = NewsItem(
            id=uuid4(),
            title=x["title"],
            thesis=s["thesis"],
            bullets=s["bullets"],
            body_md=state.content,
            url=x.get("url"),
            source_name=x["source"],
            published_at=_parse_dt(x.get("published_at")),
            raw_path=state.raw_path,
            content_hash=state.content_hash,
            region=c["region"],
            bucket=c["bucket"],
            confidence=c.get("confidence", "mid"),
            sentiment=c.get("sentiment"),
            meta={"rationale": c.get("rationale"), "language": x.get("language")},
        )
        db.add(news)
        await db.flush()
        state.news_id = news.id

        # Industries
        for ind_in in c.get("industries", []):
            ind = (await db.execute(select(Industry).where(Industry.slug == ind_in["slug"]))).scalar_one_or_none()
            if not ind:
                # auto-spawn unknown industry — operator can rename later
                ind = Industry(slug=ind_in["slug"], name=ind_in["slug"].replace("-", " ").title())
                db.add(ind)
                await db.flush()
            db.add(NewsIndustry(news_id=news.id, industry_id=ind.id, relevance=ind_in.get("relevance", 1.0)))

        # Entities
        for ent_in in c.get("entities", []):
            slug = _slugify(ent_in["name"], ent_in.get("ticker"))
            ent = (await db.execute(select(Entity).where(Entity.slug == slug))).scalar_one_or_none()
            if not ent:
                ent = Entity(
                    id=uuid4(),
                    slug=slug,
                    name=ent_in["name"],
                    kind=ent_in.get("kind", "company"),
                    ticker=ent_in.get("ticker"),
                )
                db.add(ent)
                await db.flush()
            db.add(NewsEntity(news_id=news.id, entity_id=ent.id, relevance=ent_in.get("relevance", 1.0)))

        # Embedding
        if state.embedding is not None:
            db.add(Embedding(id=uuid4(), news_id=news.id, model="text-embedding-3-large", vector=state.embedding))

        await db.commit()

    state.record_step("persist", "done", latency_ms=int((time.perf_counter() - t0) * 1000))
    return state


def _parse_dt(value):
    if not value:
        return datetime.utcnow()
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return datetime.utcnow()


def _slugify(name: str, ticker: str | None) -> str:
    base = ticker.lower() if ticker else name.lower()
    return "".join(c if c.isalnum() else "-" for c in base).strip("-")[:96]
