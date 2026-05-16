"""n8n → API callback endpoints."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Request

from app.core.security import verify_internal_signature
from app.ws.manager import ws_manager

router = APIRouter()
log = structlog.get_logger()


@router.post("/n8n/job-complete")
async def n8n_job_complete(request: Request) -> dict:
    body = await request.body()
    verify_internal_signature(body, request.headers.get("X-Internal-Signature"))
    payload = await request.json()
    log.info("webhook.n8n.complete", **payload)
    if payload.get("type") == "report.ready":
        await ws_manager.broadcast("report.ready", payload)
    elif payload.get("type") == "pdf.ready":
        await ws_manager.broadcast("pdf.ready", payload)
    return {"received": True}
