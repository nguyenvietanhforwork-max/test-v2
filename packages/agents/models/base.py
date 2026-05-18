"""Provider-agnostic chat + embedding interface.

Every node in the LangGraph pipeline calls into one of these methods. The
concrete provider is selected by the `model` argument (prefix-routed) so the
caller can request `claude-sonnet-4-6` or `gpt-4o-mini` interchangeably.
"""

from __future__ import annotations

from typing import Any, Protocol


class ChatModel(Protocol):
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
        """Return {"text": str, "tokens_in": int, "tokens_out": int, "tool_calls": [...]}.

        Implementations MUST honor the JSON schema in `response_format` when provided.
        Implementations SHOULD retry transient failures with tenacity.
        """


class EmbeddingModel(Protocol):
    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        """Return one vector per input. Length must equal `EMBEDDING_DIM` (3072)."""
