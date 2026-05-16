"""Weekly synthesis report — cross-sector thematic write-up across last 7 days."""

from __future__ import annotations

from datetime import date, timedelta


async def build_last_week() -> dict:
    """Stub: see daily_brief.build_for for the full pattern; the weekly version

    1. pulls all news_items for the trailing 7 days,
    2. clusters by industry + macro topic,
    3. asks an agent to write a 'theme of the week' synthesis per cluster,
    4. composes the master markdown, persists, renders PDF.
    """
    end = date.today()
    start = end - timedelta(days=7)
    return {"status": "stub", "from": start.isoformat(), "to": end.isoformat()}
