"""Knowledge graph service."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Entity, NewsEntity, NewsItem


async def slice(  # noqa: A001
    db: AsyncSession,
    *,
    center: str | None,
    depth: int,
    window: Literal["24h", "7d", "30d", "all"],
) -> dict:
    since = _window_start(window)

    # Top N entities by mention count in the window
    stmt = (
        select(Entity.slug, Entity.name, func.count(NewsEntity.news_id).label("mentions"))
        .join(NewsEntity, NewsEntity.entity_id == Entity.id)
        .join(NewsItem, NewsItem.id == NewsEntity.news_id)
        .where(NewsItem.published_at >= since if since else True)
        .group_by(Entity.id)
        .order_by(func.count(NewsEntity.news_id).desc())
        .limit(80)
    )
    rows = (await db.execute(stmt)).all()
    nodes = [{"id": r.slug, "label": r.name, "kind": "entity", "weight": r.mentions} for r in rows]

    # Edges: entity co-occurrence in the same news item
    # Skeleton — in prod, materialize into entity_cooccurrence + read here.
    edges: list[dict] = []

    return {"nodes": nodes, "edges": edges}


def _window_start(window: str) -> datetime | None:
    if window == "all":
        return None
    delta = {"24h": 1, "7d": 7, "30d": 30}[window]
    return datetime.utcnow() - timedelta(days=delta)
