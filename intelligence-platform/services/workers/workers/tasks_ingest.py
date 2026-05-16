"""Retryable ingest tasks: full vault rescan, embed-and-index."""

import os

import httpx
import structlog
from celery import shared_task

log = structlog.get_logger()


@shared_task(bind=True, name="workers.ingest.embed_and_index", autoretry_for=(Exception,),
             retry_backoff=True, retry_backoff_max=300, retry_jitter=True, max_retries=5)
def embed_and_index(self, news_item_id: str) -> dict:
    """Compute embedding for a news_item and upsert into pgvector + meilisearch."""
    api = os.environ["API_BASE_URL"]
    with httpx.Client(timeout=30) as c:
        # placeholder for an internal API endpoint that owns embedding logic
        r = c.post(f"{api}/v1/internal/embed", json={"news_item_id": news_item_id})
        r.raise_for_status()
        return r.json()
