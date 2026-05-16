"""News list / detail / trace-back endpoints."""

import urllib.parse
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.db import get_session
from app.models.news import NewsItem, Report
from app.schemas.news import NewsItemOut, NewsListResponse, TraceBack

router = APIRouter()


@router.get("", response_model=NewsListResponse)
async def list_news(
    session: Annotated[AsyncSession, Depends(get_session)],
    bucket: str | None = Query(default=None),
    industry: list[str] = Query(default=[]),
    country: list[str] = Query(default=[]),
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=50, le=200),
    cursor: str | None = None,
) -> NewsListResponse:
    stmt = (
        select(NewsItem)
        .options(selectinload(NewsItem.classification), selectinload(NewsItem.summary))
        .order_by(desc(NewsItem.publish_date), desc(NewsItem.created_at))
    )
    if date_from:
        stmt = stmt.where(NewsItem.publish_date >= date_from)
    if date_to:
        stmt = stmt.where(NewsItem.publish_date <= date_to)
    # bucket / industry filters require classification join — kept simple here.
    if bucket:
        stmt = stmt.join(NewsItem.classification).where(NewsItem.classification.has(bucket=bucket))
    stmt = stmt.limit(limit)
    rows = (await session.scalars(stmt)).unique().all()
    items = [_to_out(r) for r in rows]
    return NewsListResponse(items=items, total=len(items), cursor=None)


@router.get("/{news_id}", response_model=NewsItemOut)
async def get_news(
    news_id: UUID, session: Annotated[AsyncSession, Depends(get_session)]
) -> NewsItemOut:
    item = await session.scalar(
        select(NewsItem)
        .options(selectinload(NewsItem.classification), selectinload(NewsItem.summary))
        .where(NewsItem.id == news_id)
    )
    if not item:
        raise HTTPException(404, "not found")
    return _to_out(item)


@router.get("/{news_id}/trace", response_model=TraceBack)
async def trace_back(
    news_id: UUID, session: Annotated[AsyncSession, Depends(get_session)]
) -> TraceBack:
    item = await session.scalar(select(NewsItem).where(NewsItem.id == news_id))
    if not item:
        raise HTTPException(404, "not found")

    vault_name = settings.vault_path.rstrip("/").split("/")[-1] or "vault"
    encoded_file = urllib.parse.quote(item.vault_path)
    obsidian_uri = f"obsidian://open?vault={vault_name}&file={encoded_file}"

    return TraceBack(
        news_item_id=item.id,
        source_url=item.source_url,
        vault_path=item.vault_path,
        obsidian_uri=obsidian_uri,
        report_ids=[],
        related_wiki_slugs=[],
    )


def _to_out(item: NewsItem) -> NewsItemOut:
    return NewsItemOut.model_validate(
        {
            "id": item.id,
            "title": item.title,
            "publish_date": item.publish_date,
            "source_url": item.source_url,
            "language": item.language,
            "status": item.status.value,
            "created_at": item.created_at,
            "classification": _classification_dict(item),
            "summary": _summary_dict(item),
        }
    )


def _classification_dict(item: NewsItem) -> dict | None:
    c = item.classification
    if not c:
        return None
    return {
        "bucket": c.bucket.value,
        "industries": c.industries,
        "countries": c.countries,
        "companies": c.companies,
        "confidence": c.confidence,
    }


def _summary_dict(item: NewsItem) -> dict | None:
    s = item.summary
    if not s:
        return None
    return {
        "thesis": s.thesis,
        "supporting_points": s.supporting_points,
        "implications": s.implications,
        "data_points": s.data_points,
    }
