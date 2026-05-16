"""Ingestion node: load the NewsItem row, parse frontmatter, detect language."""

from agents.db import fetch_news_item
from agents.utils.lang import detect_language


async def ingestion_agent(state: dict) -> dict:
    news = await fetch_news_item(state["news_item_id"])
    return {
        "raw_text": news.raw_text,
        "language": news.language or detect_language(news.raw_text),
    }
