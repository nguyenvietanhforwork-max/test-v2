"""/news/* endpoints — feed, single, manual refresh."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.core.deps import DB
from app.schemas.news import NewsFeedOut, NewsItemOut
from app.services import ingest as ingest_svc
from app.services import news as news_svc
from app.services import reports as reports_svc
from app.services.storage import storage

router = APIRouter()


@router.get("", response_model=NewsFeedOut)
async def list_news(
    db: DB,
    date_: Annotated[date | None, Query(alias="date")] = None,
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: date | None = None,
    industry: str | None = None,
    entity: str | None = None,
    region: str | None = None,
    bucket: str | None = None,
    q: str | None = None,
    cursor: str | None = None,
    limit: int = Query(50, le=100),
) -> NewsFeedOut:
    return await news_svc.list_feed(
        db,
        date_=date_,
        date_from=from_,
        date_to=to,
        industry=industry,
        entity=entity,
        region=region,
        bucket=bucket,
        q=q,
        cursor=cursor,
        limit=limit,
    )


@router.get("/{news_id}", response_model=NewsItemOut)
async def get_news(news_id: UUID, db: DB) -> NewsItemOut:
    item = await news_svc.get(db, news_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "news item not found")
    return item


@router.get("/{news_id}/summary.pdf")
async def get_news_summary_pdf(news_id: UUID, db: DB) -> RedirectResponse:
    item = await news_svc.get(db, news_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "news item not found")

    markdown = _render_a4_summary(item)
    object_key = await reports_svc.render_markdown_pdf(
        markdown,
        filename=f"article-{news_id}.pdf",
    )
    return RedirectResponse(url=await storage().get_pdf_url(object_key), status_code=status.HTTP_302_FOUND)


@router.post("/refresh", status_code=status.HTTP_202_ACCEPTED)
async def refresh_vault() -> dict[str, str]:
    job_id = await ingest_svc.trigger_full_rescan()
    return {"job_id": job_id, "status": "queued"}


def _render_a4_summary(item: NewsItemOut) -> str:
    entities = ", ".join([entity.ticker or entity.name for entity in item.entities]) or "N/A"
    source_url = item.source.url or ""
    lines = [
        f"# {item.title}",
        "",
        f"**Summary.** {item.thesis}",
        "",
        "## Arguments",
        "",
    ]
    lines.extend([f"- {bullet}" for bullet in item.bullets])
    lines.extend(
        [
            "",
            "## Implications",
            "",
            f"- Region: {item.region.value}; category: {item.bucket.value}.",
            f"- Primary industry: {item.industry}.",
            f"- Entities: {entities}.",
            f"- Confidence: {item.confidence.value}.",
            "",
            "## Source",
            "",
            f"- [{item.source.name}]({source_url})",
            f"- Raw path: `{item.raw_path}`",
        ]
    )
    return "\n".join(lines)
