"""Aggregated dashboard payload — one round trip for the daily view."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_session
from app.models.news import Bucket, Classification, NewsItem, Report, ReportType
from app.schemas.news import DashboardToday

router = APIRouter()


@router.get("/today", response_model=DashboardToday)
async def dashboard_today(
    session: Annotated[AsyncSession, Depends(get_session)],
    on: date | None = None,
) -> DashboardToday:
    target = on or date.today()

    # bucket counts
    bucket_rows = (
        await session.execute(
            select(Classification.bucket, func.count())
            .join(NewsItem, NewsItem.id == Classification.news_item_id)
            .where(NewsItem.publish_date == target)
            .group_by(Classification.bucket)
        )
    ).all()
    buckets: dict[str, dict] = {b.value: {"count": 0, "by_industry": {}} for b in Bucket}
    for bucket, count in bucket_rows:
        buckets[bucket.value]["count"] = count

    # industry breakdown for vn_corp
    industry_rows = await session.execute(
        select(func.unnest(Classification.industries), func.count())
        .join(NewsItem, NewsItem.id == Classification.news_item_id)
        .where(
            NewsItem.publish_date == target,
            Classification.bucket == Bucket.vn_corp,
        )
        .group_by(func.unnest(Classification.industries))
    )
    buckets["vn_corp"]["by_industry"] = {ind: cnt for ind, cnt in industry_rows.all()}

    # master report
    master = await session.scalar(
        select(Report)
        .where(Report.date == target, Report.type == ReportType.master)
        .order_by(Report.version.desc())
        .limit(1)
    )

    # recent items
    recent_rows = (
        await session.scalars(
            select(NewsItem)
            .options(
                selectinload(NewsItem.classification),
                selectinload(NewsItem.summary),
            )
            .where(NewsItem.publish_date == target)
            .order_by(NewsItem.created_at.desc())
            .limit(20)
        )
    ).all()

    headline = None
    if recent_rows:
        top = recent_rows[0]
        headline = {
            "news_item_id": str(top.id),
            "title": top.title,
            "thesis": top.summary.thesis if top.summary else None,
        }

    return DashboardToday(
        date=target,
        headline=headline,
        buckets=buckets,
        master_report=(
            {"id": str(master.id), "pdf_url": master.pdf_url, "version": master.version}
            if master
            else None
        ),
        recent_items=[_news_to_out(r) for r in recent_rows],
    )


def _news_to_out(item: NewsItem) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "publish_date": item.publish_date,
        "source_url": item.source_url,
        "language": item.language,
        "status": item.status.value,
        "created_at": item.created_at,
        "classification": (
            {
                "bucket": item.classification.bucket.value,
                "industries": item.classification.industries,
                "countries": item.classification.countries,
                "companies": item.classification.companies,
                "confidence": item.classification.confidence,
            }
            if item.classification
            else None
        ),
        "summary": (
            {
                "thesis": item.summary.thesis,
                "supporting_points": item.summary.supporting_points,
                "implications": item.summary.implications,
                "data_points": item.summary.data_points,
            }
            if item.summary
            else None
        ),
    }
