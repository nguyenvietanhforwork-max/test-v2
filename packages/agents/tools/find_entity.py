"""Tool: find_entity — resolve names/tickers/aliases to canonical entities."""

from __future__ import annotations

from typing import Any

import httpx

SCHEMA: dict[str, Any] = {
    "name": "find_entity",
    "description": "Resolve a company name, ticker, or alias to its canonical entity record. Use this when classifying news to avoid creating duplicate entities.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
        },
        "required": ["query"],
    },
}


async def call(args: dict[str, Any]) -> dict[str, Any] | None:
    async with httpx.AsyncClient(base_url="http://api:8000/api/v1") as c:
        res = await c.get(f"/entities/{args['query']}")
        if res.status_code == 404:
            return None
        return res.json()
