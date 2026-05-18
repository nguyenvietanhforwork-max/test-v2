from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models import ReportType


class ReportSourceOut(BaseModel):
    news_id: UUID = Field(serialization_alias="newsId")
    title: str
    url: str | None = None


class ReportSectionOut(BaseModel):
    id: UUID
    heading: str
    body_md: str = Field(serialization_alias="bodyMd")
    sources: list[ReportSourceOut]


class ReportOut(BaseModel):
    id: UUID
    type: ReportType
    title: str
    thesis: str
    markdown: str
    pdf_url: str | None = Field(default=None, serialization_alias="pdfUrl")
    published_at: datetime = Field(serialization_alias="publishedAt")
    version: int
    sections: list[ReportSectionOut]


class DailyBriefStat(BaseModel):
    label: str
    value: str
    delta: str | None = None
    delta_tone: str | None = Field(default=None, serialization_alias="deltaTone")
    sub: str | None = None


class DailyBriefOut(BaseModel):
    date: str
    thesis: str
    subtitle: str
    stats: list[DailyBriefStat]


class ReportBuildIn(BaseModel):
    type: ReportType
    industry: str | None = None
    entity: str | None = None
    from_: datetime | None = Field(default=None, alias="from")
    to: datetime | None = None
