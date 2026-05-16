"""Embedding wrapper — pluggable provider (OpenAI default, BGE local future)."""

import httpx

from app.core.config import settings


async def embed_text(text: str) -> list[float]:
    if not settings.openai_api_key:
        # dev fallback — zeros so dev queries don't crash
        return [0.0] * settings.embedding_dimensions
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": settings.embedding_model, "input": text},
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]
