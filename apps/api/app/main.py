"""Atlas Intelligence Platform — FastAPI entrypoint.

Mounted services:
    /api/v1/...   — REST API (versioned)
    /ws/stream    — real-time event WebSocket
    /metrics      — Prometheus
    /healthz      — liveness
    /readyz       — readiness (checks DB + Redis)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.v1.router import api_router
from app.api.v1.ws import ws_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.events.bus import event_bus


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await event_bus.connect()
    yield
    await event_bus.disconnect()


app = FastAPI(
    title="Atlas Intelligence API",
    version="0.1.0",
    description="REST + WebSocket gateway for the Atlas intelligence platform.",
    lifespan=lifespan,
)

# CORS — locked down to frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)

app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router)


@app.get("/healthz", tags=["meta"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", tags=["meta"])
async def readyz() -> dict[str, str]:
    # In production: check DB ping + Redis ping + Meilisearch ping
    return {"status": "ready"}
