"""Report service — list, fetch, build, render PDF."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

import httpx
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.models import Report, ReportSection, ReportSource
from app.services.storage import storage
from app.schemas.report import (
    DailyBriefOut,
    DailyBriefStat,
    ReportBuildIn,
    ReportOut,
    ReportSectionOut,
    ReportSourceOut,
)


def _to_out(r: Report) -> ReportOut:
    return ReportOut(
        id=r.id,
        type=r.type,
        title=r.title,
        thesis=r.thesis,
        markdown=r.markdown,
        pdf_url=f"/api/v1/reports/{r.id}/pdf" if r.pdf_object_key else None,
        published_at=r.published_at,
        version=r.version,
        sections=[
            ReportSectionOut(
                id=s.id,
                heading=s.heading,
                body_md=s.body_md,
                sources=[ReportSourceOut(news_id=src.news_id, title=src.news.title if src.news else "", url=src.news.url if src.news else None) for src in s.sources],
            )
            for s in r.sections
        ],
    )


async def list_reports(
    db: AsyncSession,
    *,
    type_: str | None,
    date_from: date | None,
    date_to: date | None,
    limit: int,
) -> list[ReportOut]:
    stmt = (
        select(Report)
        .options(selectinload(Report.sections).selectinload(ReportSection.sources).selectinload(ReportSource.news))
        .order_by(desc(Report.published_at))
        .limit(limit)
    )
    if type_:
        stmt = stmt.where(Report.type == type_)
    if date_from:
        stmt = stmt.where(Report.published_at >= date_from)
    if date_to:
        stmt = stmt.where(Report.published_at <= date_to)
    rows = (await db.execute(stmt)).scalars().all()
    return [_to_out(r) for r in rows]


async def get(db: AsyncSession, report_id: UUID) -> ReportOut | None:
    stmt = (
        select(Report)
        .options(selectinload(Report.sections).selectinload(ReportSection.sources).selectinload(ReportSource.news))
        .where(Report.id == report_id)
    )
    r = (await db.execute(stmt)).scalar_one_or_none()
    return _to_out(r) if r else None


async def get_daily_brief(db: AsyncSession, on: date | None) -> DailyBriefOut:
    """Return the morning brief structure powering the dashboard hero.

    Pulls from the latest `daily` Report; if none exists for the requested date,
    falls back to a computed summary.
    """
    target = on or datetime.utcnow().date()
    stmt = (
        select(Report)
        .where(Report.type == "daily")
        .where(Report.published_at >= target)
        .order_by(desc(Report.published_at))
        .limit(1)
    )
    r = (await db.execute(stmt)).scalar_one_or_none()

    if not r:
        return DailyBriefOut(
            date=target.isoformat(),
            thesis="No brief published yet. Pipeline is still ingesting today's clippings.",
            subtitle="Drop a clipping into raw/news/ or trigger /vault/refresh.",
            stats=_default_stats(),
        )

    return DailyBriefOut(
        date=r.published_at.date().isoformat(),
        thesis=r.thesis,
        subtitle=(r.meta or {}).get("subtitle", ""),
        stats=[DailyBriefStat(**s) for s in (r.meta or {}).get("stats", [])] or _default_stats(),
    )


def _default_stats() -> list[DailyBriefStat]:
    return [
        DailyBriefStat(label="Items Today", value="0", sub="awaiting ingest"),
        DailyBriefStat(label="Active Industries", value="0", sub=""),
        DailyBriefStat(label="Sentiment Index", value="—", sub=""),
        DailyBriefStat(label="Pipeline P95", value="—", sub=""),
    ]


async def get_pdf_url(db: AsyncSession, report_id: UUID) -> str | None:
    """Return a stable downloadable PDF URL, rendering on demand when needed."""
    report = await db.get(Report, report_id)
    if not report:
        return None

    if not report.pdf_object_key:
        report.pdf_object_key = await render_markdown_pdf(
            report.markdown,
            filename=f"report-{report.id}.pdf",
        )
        await db.commit()

    return await storage().get_pdf_url(report.pdf_object_key)


async def render_markdown_pdf(markdown: str, *, filename: str) -> str:
    """Ask the PDF microservice to render markdown and persist it to object storage."""
    async with httpx.AsyncClient(base_url=settings.PDF_SERVICE_URL, timeout=120.0) as c:
        res = await c.post("/render", json={"markdown": markdown, "filename": filename})
        res.raise_for_status()
        return res.json()["object_key"]


async def trigger_build(body: ReportBuildIn) -> str:
    """Enqueue a Celery task to build the requested report."""
    job_id = str(uuid4())
    # In production: celery.send_task("atlas.reports.build", kwargs={...}, task_id=job_id)
    return job_id
