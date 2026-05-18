"""PDF generation: calls the PDF engine over HTTP."""

import httpx
import structlog

from agents.config import settings
from agents.db import update_report_pdf

log = structlog.get_logger()


async def pdf_generation_agent(state: dict) -> dict:
    report_inclusion = state.get("report_inclusion") or {}
    report_id = report_inclusion.get("report_id")
    if not report_id:
        return {"pdf_url": None}
    body_md = report_inclusion.get("body_md", "")

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{settings.pdf_engine_url}/render",
            json={
                "template": "master-report",
                "data": {"body_md": body_md, "report_id": report_id},
                "options": {"upload": True},
            },
        )
        resp.raise_for_status()
        url = resp.json().get("url")

    if url:
        await update_report_pdf(report_id=report_id, pdf_url=url)
    return {"pdf_url": url}
