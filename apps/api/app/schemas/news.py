from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models import Bucket, Confidence, Region


class SourceOut(BaseModel):
    name: str
    url: str | None = None


class EntityOut(BaseModel):
    slug: str
    name: str
    ticker: str | None = None
    exchange: str | None = None


class IndustryOut(BaseModel):
    slug: str
    name: str
    color: str | None = None


class NewsItemOut(BaseModel):
    id: UUID
    title: str
    thesis: str
    bullets: list[str]
    published_at: datetime = Field(serialization_alias="publishedAt")
    source: SourceOut
    industry: str
    industries: list[IndustryOut]
    entities: list[EntityOut]
    region: Region
    bucket: Bucket
    confidence: Confidence
    raw_path: str = Field(serialization_alias="rawPath")
    wiki_path: str | None = Field(default=None, serialization_alias="wikiPath")


class NewsFeedOut(BaseModel):
    items: list[NewsItemOut]
    next_cursor: str | None = Field(default=None, serialization_alias="nextCursor")
