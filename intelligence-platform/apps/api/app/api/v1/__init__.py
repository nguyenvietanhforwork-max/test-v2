from fastapi import APIRouter

from app.api.v1.routes import dashboard, graph, ingest, news, reports, search, webhooks
from app.ws.routes import router as ws_router

router = APIRouter()
router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
router.include_router(news.router, prefix="/news", tags=["news"])
router.include_router(reports.router, prefix="/reports", tags=["reports"])
router.include_router(search.router, prefix="/search", tags=["search"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
router.include_router(graph.router, prefix="/graph", tags=["graph"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
router.include_router(ws_router, tags=["ws"])
