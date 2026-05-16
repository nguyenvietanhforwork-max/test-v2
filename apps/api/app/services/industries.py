"""Industry service — list, slug lookup, heatmap aggregation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Industry, NewsIndustry, NewsItem


async def list_all(db: AsyncSession) -> list[dict]:
    rows = (await db.execute(select(Industry).order_by(Industry.name))).scalars().all()
    return [{"slug": r.slug, "name": r.name, "color": r.color} for r in rows]


async def get_by_slug(db: AsyncSession, slug: str) -> dict:
    r = (await db.execute(select(Industry).where(Industry.slug == slug))).scalar_one_or_none()
    if not r:
        return {}
    return {"slug": r.slug, "name": r.name, "color": r.color, "description": r.description}


async def heatmap(db: AsyncSession, *, window: Literal["1d", "7d", "30d"]) -> dict:
    delta = {"1d": 1, "7d": 7, "30d": 30}[window]
    since = datetime.utcnow() - timedelta(days=delta)

    stmt = (
        select(
            Industry.slug,
            Industry.name,
            Industry.color,
            func.count(NewsItem.id).label("volume"),
            func.coalesce(func.avg(NewsItem.sentiment), 0).label("sentiment"),
        )
        .join(NewsIndustry, NewsIndustry.industry_id == Industry.id, isouter=True)
        .join(NewsItem, NewsItem.id == NewsIndustry.news_id, isouter=True)
        .where((NewsItem.published_at.is_(None)) | (NewsItem.published_at >= since))
        .group_by(Industry.id)
        .order_by(Industry.name)
    )
    rows = (await db.execute(stmt)).all()
    cells = [
        {"slug": r.slug, "name": r.name, "color": r.color or "#A1A1AA", "volume": int(r.volume), "sentiment": float(r.sentiment)}
        for r in rows
    ]
    return {"window": window, "cells": cells}
