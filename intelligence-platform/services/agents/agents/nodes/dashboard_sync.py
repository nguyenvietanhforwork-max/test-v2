"""Final node: emit WS events + archive raw file."""

import httpx
import structlog

from agents.config import settings
from agents.db import mark_news_status

log = structlog.get_logger()


async def dashboard_sync_agent(state: dict) -> dict:
    await mark_news_status(state["news_item_id"], "reported")

    # tell API to broadcast WS events (api owns the fan-out)
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            await c.post(
                f"{settings.api_base_url}/v1/webhooks/n8n/job-complete",
                json={"type": "news.classified", "data": state.get("classification", {})},
            )
    except Exception as e:
        log.warning("sync.api_ping_failed", error=str(e))

    return {}
