"""High-level entrypoint called by n8n daily-report workflow."""

import httpx
import structlog

from agents.config import settings
from agents.nodes.report_generation import render_daily_report

log = structlog.get_logger()


async def build_report_for_date(date_, report_type: str, force: bool) -> str | None:
    body_md = await render_daily_report(str(date_), report_type)
    if not body_md:
        return None

    # render PDF
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            resp = await c.post(
                f"{settings.pdf_engine_url}/render",
                json={"template": "master-report", "data": {"body_md": body_md}},
            )
            resp.raise_for_status()
            log.info("report.pdf_rendered", url=resp.json().get("url"))
    except Exception as e:
        log.error("report.pdf_failed", error=str(e))

    return body_md[:120]
