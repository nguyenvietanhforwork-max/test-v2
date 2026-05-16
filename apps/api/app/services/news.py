"""News service — feed listing, single fetch, related queries."""

from __future__ import annotations

import base64
import json
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Entity, Industry, NewsEntity, NewsIndustry, NewsItem
from app.schemas.news import (
    EntityOut,
    IndustryOut,
    NewsFeedOut,
    NewsItemOut,
    SourceOut,
)


def _to_out(n: NewsItem) -> NewsItemOut:
    return NewsItemOut(
        id=n.id,
        title=n.title,
        thesis=n.thesis,
        bullets=n.bullets or [],
        published_at=n.published_at,
        source=SourceOut(name=n.source_name, url=n.url),
        industry=(n.industries[0].industry.slug if n.industries else "other"),
        industries=[IndustryOut(slug=ni.industry.slug, name=ni.industry.name, color=ni.industry.color) for ni in n.industries],
        entities=[
            EntityOut(slug=ne.entity.slug, name=ne.entity.name, ticker=ne.entity.ticker, exchange=ne.entity.exchange)
            for ne in n.entities
        ],
        region=n.region,
        bucket=n.bucket,
        confidence=n.confidence,
        raw_path=n.raw_path,
        wiki_path=n.wiki_path,
    )


def _encode_cursor(news: NewsItem) -> str:
    return base64.urlsafe_b64encode(
        json.dumps({"ts": news.published_at.isoformat(), "id": str(news.id)}).encode()
    ).decode()


def _decode_cursor(c: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(c.encode()))


async def list_feed(
    db: AsyncSession,
    *,
    date_: date | None,
    date_from: date | None,
    date_to: date | None,
    industry: str | None,
    entity: str | None,
    region: str | None,
    bucket: str | None,
    q: str | None,
    cursor: str | None,
    limit: int,
) -> NewsFeedOut:
    stmt = (
        select(NewsItem)
        .options(
            selectinload(NewsItem.industries).selectinload(NewsIndustry.industry),
            selectinload(NewsItem.entities).selectinload(NewsEntity.entity),
        )
        .where(NewsItem.archived.is_(False))
        .order_by(desc(NewsItem.published_at))
        .limit(limit + 1)
    )

    if date_:
        stmt = stmt.where(NewsItem.published_at >= date_).where(NewsItem.published_at < date_ + timedelta(days=1))
    if date_from:
        stmt = stmt.where(NewsItem.published_at >= date_from)
    if date_to:
        stmt = stmt.where(NewsItem.published_at <= date_to)
    if region:
        stmt = stmt.where(NewsItem.region == region)
    if bucket:
        stmt = stmt.where(NewsItem.bucket == bucket)
    if q:
        stmt = stmt.where(NewsItem.title.ilike(f"%{q}%") | NewsItem.thesis.ilike(f"%{q}%"))
    if industry:
        stmt = stmt.join(NewsItem.industries).join(NewsIndustry.industry).where(Industry.slug == industry)
    if entity:
        stmt = stmt.join(NewsItem.entities).join(NewsEntity.entity).where(Entity.slug == entity)

    if cursor:
        c = _decode_cursor(cursor)
        stmt = stmt.where(NewsItem.published_at < c["ts"])

    rows = (await db.execute(stmt)).scalars().all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    return NewsFeedOut(
        items=[_to_out(r) for r in rows],
        next_cursor=_encode_cursor(rows[-1]) if has_more and rows else None,
    )


async def get(db: AsyncSession, news_id: UUID) -> NewsItemOut | None:
    stmt = (
        select(NewsItem)
        .options(
            selectinload(NewsItem.industries).selectinload(NewsIndustry.industry),
            selectinload(NewsItem.entities).selectinload(NewsEntity.entity),
        )
        .where(NewsItem.id == news_id)
    )
    r = (await db.execute(stmt)).scalar_one_or_none()
    return _to_out(r) if r else None
