"""Ingest endpoint: watcher → API → DB + n8n webhook trigger."""

import uuid
from typing import Annotated

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.models.news import NewsItem, NewsStatus
from app.schemas.news import IngestRequest, IngestResponse
from app.ws.manager import ws_manager

router = APIRouter()
log = structlog.get_logger()


@router.post("", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest(
    payload: IngestRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> IngestResponse:
    # de-dupe by content hash
    existing = await session.scalar(
        select(NewsItem).where(NewsItem.content_hash == payload.content_hash)
    )
    if existing:
        log.info("ingest.duplicate", id=str(existing.id))
        return IngestResponse(id=existing.id, status="duplicate", pipeline_run_id="")

    item = NewsItem(
        content_hash=payload.content_hash,
        vault_path=payload.vault_path,
        source_url=str(payload.source_url) if payload.source_url else None,
        title=payload.title,
        publish_date=payload.publish_date,
        language=payload.language,
        raw_text=payload.raw_text,
        status=NewsStatus.queued,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)

    pipeline_run_id = f"pr_{uuid.uuid4().hex[:12]}"

    # fan-out: notify WebSocket subscribers + trigger n8n
    await ws_manager.broadcast(
        "news.ingested",
        {"id": str(item.id), "title": item.title, "publish_date": str(item.publish_date)},
    )
    await _trigger_n8n(item.id, pipeline_run_id)

    return IngestResponse(id=item.id, status="queued", pipeline_run_id=pipeline_run_id)


async def _trigger_n8n(news_item_id: uuid.UUID, pipeline_run_id: str) -> None:
    if not settings.n8n_webhook_url:
        log.warning("n8n.webhook_unset")
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{settings.n8n_webhook_url}/ingest-news",
                json={"news_item_id": str(news_item_id), "pipeline_run_id": pipeline_run_id},
                headers={"X-API-Key": settings.n8n_api_key or ""},
            )
    except httpx.HTTPError as e:
        log.error("n8n.trigger_failed", error=str(e))
        # don't raise — n8n missing should not block ingestion; the daily resync job
        # will pick up unprocessed items.


@router.post("/refresh", status_code=status.HTTP_202_ACCEPTED)
async def manual_refresh(session: Annotated[AsyncSession, Depends(get_session)]) -> dict:
    """Rescan vault — finds items missing from DB and re-emits ingest events.
    Implementation lives in the watcher; this endpoint just signals it via Redis."""
    # publish to events.control stream
    from app.services.events import publish_event

    await publish_event("control.rescan", {"requested_by": "api"})
    return {"status": "scheduled"}
