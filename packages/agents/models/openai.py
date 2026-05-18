"""OpenAI chat + embeddings backend (used as fallback and for embeddings)."""

from __future__ import annotations

import os
from typing import Any

from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class OpenAIChat:
    def __init__(self, api_key: str | None = None) -> None:
        self.client = AsyncOpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), retry=retry_if_exception_type(Exception), reraise=True)
    async def chat(
        self,
        *,
        system: str,
        user: str,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.2,
        tools: list[dict] | None = None,
        response_format: dict | None = None,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": model or "gpt-4o-mini",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if response_format:
            kwargs["response_format"] = response_format
        if tools:
            kwargs["tools"] = tools

        res = await self.client.chat.completions.create(**kwargs)
        choice = res.choices[0]
        return {
            "text": choice.message.content or "",
            "tokens_in": res.usage.prompt_tokens,
            "tokens_out": res.usage.completion_tokens,
            "tool_calls": [],
            "stop_reason": choice.finish_reason,
        }


class OpenAIEmbeddings:
    def __init__(self, api_key: str | None = None) -> None:
        self.client = AsyncOpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), retry=retry_if_exception_type(Exception), reraise=True)
    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        res = await self.client.embeddings.create(
            input=texts, model=model or "text-embedding-3-large"
        )
        # Sort by index to preserve order
        sorted_data = sorted(res.data, key=lambda d: d.index)
        return [d.embedding for d in sorted_data]
