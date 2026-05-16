"""LLM provider selection — model-prefix routed.

Usage:
    chat = get_chat("claude-sonnet-4-6")     # → AnthropicChat
    chat = get_chat("gpt-4o-mini")           # → OpenAIChat
    emb  = get_embeddings()                  # → OpenAIEmbeddings
"""

from __future__ import annotations

from functools import lru_cache

from .anthropic import AnthropicChat
from .openai import OpenAIChat, OpenAIEmbeddings


@lru_cache
def _claude() -> AnthropicChat:
    return AnthropicChat()


@lru_cache
def _openai() -> OpenAIChat:
    return OpenAIChat()


@lru_cache
def _embed() -> OpenAIEmbeddings:
    return OpenAIEmbeddings()


def get_chat(model: str):
    if model.startswith("claude"):
        return _claude()
    if model.startswith("gpt") or model.startswith("o"):
        return _openai()
    raise ValueError(f"unknown model family for {model!r}")


def get_embeddings() -> OpenAIEmbeddings:
    return _embed()
