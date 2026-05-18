"""/reports/* endpoints."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.core.deps import DB
from app.schemas.report import DailyBriefOut, ReportBuildIn, ReportOut
from app.services import reports as reports_svc

router = APIRouter()


@router.get("", response_model=list[ReportOut])
async def list_reports(
    db: DB,
    type_: Annotated[str | None, Query(alias="type")] = None,
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: date | None = None,
    limit: int = Query(20, le=100),
) -> list[ReportOut]:
    return await reports_svc.list_reports(db, type_=type_, date_from=from_, date_to=to, limit=limit)


@router.get("/daily", response_model=DailyBriefOut)
async def get_daily_brief(db: DB, date_: date | None = Query(default=None, alias="date")) -> DailyBriefOut:
    return await reports_svc.get_daily_brief(db, on=date_)


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(report_id: UUID, db: DB) -> ReportOut:
    r = await reports_svc.get(db, report_id)
    if not r:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "report not found")
    return r


@router.get("/{report_id}/pdf")
async def get_report_pdf(report_id: UUID, db: DB) -> RedirectResponse:
    url = await reports_svc.get_pdf_url(db, report_id)
    if not url:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "report not found")
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.post("/build", status_code=status.HTTP_202_ACCEPTED)
async def build_report(body: ReportBuildIn) -> dict[str, str]:
    job_id = await reports_svc.trigger_build(body)
    return {"job_id": job_id, "status": "queued"}
