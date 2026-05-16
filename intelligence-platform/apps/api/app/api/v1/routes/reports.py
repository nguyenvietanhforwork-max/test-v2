"""Report list / detail / regenerate / PDF redirect."""

from datetime import date
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.models.news import Report, ReportType
from app.schemas.news import ReportOut

router = APIRouter()


@router.get("", response_model=list[ReportOut])
async def list_reports(
    session: Annotated[AsyncSession, Depends(get_session)],
    date_from: date | None = None,
    type: ReportType | None = None,
    limit: int = 30,
) -> list[ReportOut]:
    stmt = select(Report).order_by(desc(Report.date)).limit(limit)
    if date_from:
        stmt = stmt.where(Report.date >= date_from)
    if type:
        stmt = stmt.where(Report.type == type)
    rows = (await session.scalars(stmt)).all()
    return [ReportOut.model_validate(_to_dict(r)) for r in rows]


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: UUID, session: Annotated[AsyncSession, Depends(get_session)]
) -> ReportOut:
    r = await session.scalar(select(Report).where(Report.id == report_id))
    if not r:
        raise HTTPException(404)
    return ReportOut.model_validate(_to_dict(r))


@router.get("/{report_id}/pdf")
async def report_pdf(
    report_id: UUID, session: Annotated[AsyncSession, Depends(get_session)]
):
    r = await session.scalar(select(Report).where(Report.id == report_id))
    if not r:
        raise HTTPException(404)
    if r.pdf_url:
        return RedirectResponse(r.pdf_url)
    # synchronous render fallback
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{settings.pdf_engine_url}/render",
            json={"template": "master-report", "data": {"body_md": r.body_md}},
        )
        resp.raise_for_status()
        return RedirectResponse(resp.json()["url"])


@router.post("/regenerate", status_code=202)
async def regenerate(date_: date) -> dict:
    """Asks the agents service to rebuild reports for a given date."""
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            f"{settings.agents_base_url}/build-report",
            json={"date": str(date_), "type": "master", "force": True},
        )
    return {"status": "scheduled", "date": str(date_)}


def _to_dict(r: Report) -> dict:
    return {
        "id": r.id,
        "date": r.date,
        "type": r.type.value,
        "body_md": r.body_md,
        "pdf_url": r.pdf_url,
        "version": r.version,
    }
