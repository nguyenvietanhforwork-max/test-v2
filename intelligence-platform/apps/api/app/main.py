"""FastAPI entrypoint for the Intelligence Platform public API."""

from contextlib import asynccontextmanager

import sentry_sdk
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as v1_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.ws.manager import ws_manager

configure_logging()
log = structlog.get_logger()

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("api.startup", env=settings.env)
    await ws_manager.start()
    yield
    await ws_manager.stop()
    log.info("api.shutdown")


app = FastAPI(
    title="Intelligence Platform API",
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/v1")


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "version": app.version}


@app.get("/readyz")
async def readyz():
    # TODO: ping db + redis
    return {"status": "ready"}
