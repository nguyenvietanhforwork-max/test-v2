"""Pydantic schemas for news/reports endpoints."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class IngestRequest(BaseModel):
    vault_path: str
    content_hash: str = Field(..., description="sha256: prefixed")
    source_url: HttpUrl | None = None
    title: str
    publish_date: date | None = None
    raw_text: str
    language: Literal["vi", "en"] = "vi"


class IngestResponse(BaseModel):
    id: UUID
    status: str
    pipeline_run_id: str


class SupportingPoint(BaseModel):
    text: str
    citation_offsets: tuple[int, int] | None = None


class StructuredSummary(BaseModel):
    thesis: str
    supporting_points: list[SupportingPoint]
    implications: list[SupportingPoint]
    data_points: list[SupportingPoint] = []


class ClassificationOut(BaseModel):
    bucket: Literal["vn_corp", "intl_corp", "vn_macro", "intl_macro"]
    industries: list[str]
    countries: list[str]
    companies: list[str]
    confidence: float


class NewsItemOut(BaseModel):
    id: UUID
    title: str
    publish_date: date | None
    source_url: HttpUrl | None
    language: str
    status: str
    created_at: datetime
    classification: ClassificationOut | None = None
    summary: StructuredSummary | None = None


class NewsListResponse(BaseModel):
    items: list[NewsItemOut]
    total: int
    cursor: str | None = None


class TraceBack(BaseModel):
    news_item_id: UUID
    source_url: HttpUrl | None
    vault_path: str
    obsidian_uri: str
    report_ids: list[UUID]
    related_wiki_slugs: list[str]


class DashboardToday(BaseModel):
    date: date
    headline: dict | None
    buckets: dict[str, dict]
    master_report: dict | None
    recent_items: list[NewsItemOut]


class ReportOut(BaseModel):
    id: UUID
    date: date
    type: str
    body_md: str
    pdf_url: str | None
    version: int


class SearchRequest(BaseModel):
    q: str
    filters: dict = {}
    k: int = 20


class SearchHit(BaseModel):
    news_item_id: UUID
    title: str
    snippet: str
    score: float
    publish_date: date | None
