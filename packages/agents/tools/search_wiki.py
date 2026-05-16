"""Tool: search_wiki — Anthropic tool-use callable exposed to LLM agents."""

from __future__ import annotations

from typing import Any

import httpx

SCHEMA: dict[str, Any] = {
    "name": "search_wiki",
    "description": "Search the wiki layer for existing concept/entity/source pages. Use this BEFORE creating new wiki pages to avoid duplicates.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "search terms; supports Vietnamese diacritics"},
            "kind": {"type": "string", "enum": ["concept", "entity", "source-summary", "comparison"], "description": "optional filter"},
            "limit": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
        },
        "required": ["query"],
    },
}


async def call(args: dict[str, Any]) -> list[dict[str, Any]]:
    """Execute the tool — returns a list of {path, title, kind, snippet}."""
    async with httpx.AsyncClient(base_url="http://api:8000/api/v1") as c:
        res = await c.post("/search", json={"query": args["query"], "mode": "hybrid", "limit": args.get("limit", 5)})
        res.raise_for_status()
        hits = res.json().get("hits", [])
        return [{"path": h["id"], "title": h["title"], "snippet": h.get("snippet", "")} for h in hits]
