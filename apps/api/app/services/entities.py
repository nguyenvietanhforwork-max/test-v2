"""Entity service."""

from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Entity, NewsEntity, NewsItem


async def get_by_slug(db: AsyncSession, slug: str) -> dict | None:
    e = (await db.execute(select(Entity).where(Entity.slug == slug))).scalar_one_or_none()
    if not e:
        return None
    return {
        "slug": e.slug,
        "name": e.name,
        "aliases": e.aliases,
        "ticker": e.ticker,
        "exchange": e.exchange,
        "country": e.country,
        "wiki_path": e.wiki_path,
    }


async def timeline(db: AsyncSession, slug: str, limit: int = 50) -> list[dict]:
    stmt = (
        select(NewsItem)
        .join(NewsItem.entities)
        .join(NewsEntity.entity)
        .where(Entity.slug == slug)
        .order_by(desc(NewsItem.published_at))
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {"id": str(r.id), "title": r.title, "thesis": r.thesis, "published_at": r.published_at.isoformat(), "url": r.url}
        for r in rows
    ]
