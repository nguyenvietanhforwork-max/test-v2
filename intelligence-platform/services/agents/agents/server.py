"""FastAPI shell around the LangGraph pipeline. n8n calls these endpoints."""

from datetime import date

import structlog
from fastapi import FastAPI
from pydantic import BaseModel

from agents.graph import build_graph
from agents.report import build_report_for_date

log = structlog.get_logger()
app = FastAPI(title="Intelligence Agents", version="0.1.0")
graph = build_graph()


class RunRequest(BaseModel):
    news_item_id: str
    pipeline_run_id: str


class BuildReportRequest(BaseModel):
    date: date
    type: str = "master"
    force: bool = False


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/run")
async def run_pipeline(req: RunRequest) -> dict:
    """Single-item pipeline: classify → summarize → wiki_enrich → emit."""
    log.info("agents.run.start", **req.model_dump())
    state = await graph.ainvoke({"news_item_id": req.news_item_id, "errors": []})
    log.info("agents.run.done", news_item_id=req.news_item_id)
    return {"news_item_id": req.news_item_id, "errors": state.get("errors", [])}


@app.post("/build-report")
async def build_report(req: BuildReportRequest) -> dict:
    log.info("agents.build_report.start", date=str(req.date), type=req.type)
    report_id = await build_report_for_date(req.date, req.type, req.force)
    return {"report_id": report_id, "date": str(req.date), "type": req.type}
