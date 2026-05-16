"""SQLAlchemy models for the Atlas platform.

ER overview:
    news_items 1─N news_entities N─1 entities
    news_items 1─N news_industries N─1 industries
    news_items 1─1 embeddings
    news_items 1─N report_sources N─1 reports
    reports    1─N report_sections
    pipeline_runs 1─N pipeline_steps
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base


class Region(enum.StrEnum):
    VN = "VN"
    INT = "INT"


class Bucket(enum.StrEnum):
    MACRO = "macro"
    CORP = "corp"


class Confidence(enum.StrEnum):
    LOW = "low"
    MID = "mid"
    HIGH = "high"


class ReportType(enum.StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MASTER = "master"
    INDUSTRY = "industry"
    ENTITY = "entity"


class PipelineStatus(enum.StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


# ---------- Mixins ----------


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


# ---------- Core domain ----------


class User(Base, TimestampMixin):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Industry(Base, TimestampMixin):
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    color: Mapped[str | None] = mapped_column(String(16))
    description: Mapped[str | None] = mapped_column(Text)

    news_links: Mapped[list[NewsIndustry]] = relationship(back_populates="industry")


class Entity(Base, TimestampMixin):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(96), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), default="company")  # company | person | place | other
    ticker: Mapped[str | None] = mapped_column(String(16))
    exchange: Mapped[str | None] = mapped_column(String(16))
    country: Mapped[str | None] = mapped_column(String(8))
    aliases: Mapped[list[str]] = mapped_column(JSONB, default=list)
    wiki_path: Mapped[str | None] = mapped_column(String(512))

    news_links: Mapped[list[NewsEntity]] = relationship(back_populates="entity")


class NewsItem(Base, TimestampMixin):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    thesis: Mapped[str] = mapped_column(Text, nullable=False)
    bullets: Mapped[list[str]] = mapped_column(JSONB, default=list)
    body_md: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(String(1024))
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    raw_path: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    wiki_path: Mapped[str | None] = mapped_column(String(1024))
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    region: Mapped[Region] = mapped_column(Enum(Region), nullable=False)
    bucket: Mapped[Bucket] = mapped_column(Enum(Bucket), nullable=False)
    confidence: Mapped[Confidence] = mapped_column(Enum(Confidence), default=Confidence.MID)
    sentiment: Mapped[float | None] = mapped_column(Float)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    industries: Mapped[list[NewsIndustry]] = relationship(back_populates="news", cascade="all, delete-orphan")
    entities: Mapped[list[NewsEntity]] = relationship(back_populates="news", cascade="all, delete-orphan")
    embedding: Mapped[Embedding | None] = relationship(back_populates="news", uselist=False, cascade="all, delete-orphan")
    report_sources: Mapped[list[ReportSource]] = relationship(back_populates="news")

    __table_args__ = (
        Index("ix_news_published_region_bucket", "published_at", "region", "bucket"),
    )


class NewsIndustry(Base):
    news_id: Mapped[UUID] = mapped_column(ForeignKey("news_item.id", ondelete="CASCADE"), primary_key=True)
    industry_id: Mapped[int] = mapped_column(ForeignKey("industry.id", ondelete="CASCADE"), primary_key=True)
    relevance: Mapped[float] = mapped_column(Float, default=1.0)

    news: Mapped[NewsItem] = relationship(back_populates="industries")
    industry: Mapped[Industry] = relationship(back_populates="news_links")


class NewsEntity(Base):
    news_id: Mapped[UUID] = mapped_column(ForeignKey("news_item.id", ondelete="CASCADE"), primary_key=True)
    entity_id: Mapped[UUID] = mapped_column(ForeignKey("entity.id", ondelete="CASCADE"), primary_key=True)
    relevance: Mapped[float] = mapped_column(Float, default=1.0)
    sentiment: Mapped[float | None] = mapped_column(Float)

    news: Mapped[NewsItem] = relationship(back_populates="entities")
    entity: Mapped[Entity] = relationship(back_populates="news_links")


class Embedding(Base, TimestampMixin):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    news_id: Mapped[UUID] = mapped_column(ForeignKey("news_item.id", ondelete="CASCADE"), unique=True)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    vector: Mapped[Any] = mapped_column(Vector(settings.EMBEDDING_DIM), nullable=False)

    news: Mapped[NewsItem] = relationship(back_populates="embedding")


# ---------- Reports ----------


class Report(Base, TimestampMixin):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    thesis: Mapped[str] = mapped_column(Text, nullable=False)
    markdown: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_object_key: Mapped[str | None] = mapped_column(String(512))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    sections: Mapped[list[ReportSection]] = relationship(back_populates="report", cascade="all, delete-orphan", order_by="ReportSection.position")


class ReportSection(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    report_id: Mapped[UUID] = mapped_column(ForeignKey("report.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    heading: Mapped[str] = mapped_column(String(256), nullable=False)
    body_md: Mapped[str] = mapped_column(Text, nullable=False)

    report: Mapped[Report] = relationship(back_populates="sections")
    sources: Mapped[list[ReportSource]] = relationship(back_populates="section", cascade="all, delete-orphan")


class ReportSource(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    section_id: Mapped[UUID] = mapped_column(ForeignKey("report_section.id", ondelete="CASCADE"))
    news_id: Mapped[UUID] = mapped_column(ForeignKey("news_item.id", ondelete="CASCADE"))
    citation_label: Mapped[str | None] = mapped_column(String(64))

    section: Mapped[ReportSection] = relationship(back_populates="sources")
    news: Mapped[NewsItem] = relationship(back_populates="report_sources")

    __table_args__ = (UniqueConstraint("section_id", "news_id", name="uq_section_news"),)


# ---------- Pipeline observability ----------


class PipelineRun(Base, TimestampMixin):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    news_id: Mapped[UUID | None] = mapped_column(ForeignKey("news_item.id", ondelete="SET NULL"))
    status: Mapped[PipelineStatus] = mapped_column(Enum(PipelineStatus), default=PipelineStatus.QUEUED)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)

    steps: Mapped[list[PipelineStep]] = relationship(back_populates="run", cascade="all, delete-orphan", order_by="PipelineStep.position")


class PipelineStep(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("pipeline_run.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(64))  # extract | classify | summarize | embed | persist | publish
    status: Mapped[PipelineStatus] = mapped_column(Enum(PipelineStatus))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    tokens: Mapped[int | None] = mapped_column(Integer)
    model: Mapped[str | None] = mapped_column(String(64))
    input_meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    output_meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    error: Mapped[str | None] = mapped_column(Text)

    run: Mapped[PipelineRun] = relationship(back_populates="steps")


class PipelineDeadLetter(Base, TimestampMixin):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    run_id: Mapped[UUID | None] = mapped_column(ForeignKey("pipeline_run.id", ondelete="SET NULL"))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    error: Mapped[str] = mapped_column(Text)
    traceback: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ---------- Wiki index ----------


class WikiPage(Base, TimestampMixin):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    path: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(512))
    kind: Mapped[str] = mapped_column(String(32))  # concept | entity | source-summary | comparison
    content_hash: Mapped[str] = mapped_column(String(64))
    frontmatter: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


# ---------- Audit log ----------


class AuditLog(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actor: Mapped[str] = mapped_column(String(128))  # agent name or user id
    action: Mapped[str] = mapped_column(String(64))
    target: Mapped[str] = mapped_column(String(512))
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
