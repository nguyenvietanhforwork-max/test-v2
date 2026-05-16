"""News, summaries, classifications, reports — ORM models."""

import enum
import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.models.base import Base, Timestamped, UUIDPk


class Bucket(str, enum.Enum):
    vn_corp = "vn_corp"
    intl_corp = "intl_corp"
    vn_macro = "vn_macro"
    intl_macro = "intl_macro"


class NewsStatus(str, enum.Enum):
    queued = "queued"
    classified = "classified"
    summarized = "summarized"
    reported = "reported"
    archived = "archived"
    failed = "failed"


class ReportType(str, enum.Enum):
    news = "news"
    social = "social"
    pdf = "pdf"
    master = "master"


class NewsItem(Base, UUIDPk, Timestamped):
    __tablename__ = "news_items"

    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    vault_path: Mapped[str] = mapped_column(String(1024))
    source_url: Mapped[str | None] = mapped_column(String(2048))
    title: Mapped[str] = mapped_column(String(1024))
    publish_date: Mapped[date | None] = mapped_column(Date, index=True)
    language: Mapped[str] = mapped_column(String(8), default="vi")
    raw_text: Mapped[str] = mapped_column(Text)
    status: Mapped[NewsStatus] = mapped_column(Enum(NewsStatus), default=NewsStatus.queued)

    classification: Mapped["Classification"] = relationship(
        back_populates="news_item", uselist=False
    )
    summary: Mapped["Summary"] = relationship(back_populates="news_item", uselist=False)


class Classification(Base, UUIDPk, Timestamped):
    __tablename__ = "classifications"

    news_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("news_items.id", ondelete="CASCADE"), unique=True
    )
    bucket: Mapped[Bucket] = mapped_column(Enum(Bucket), index=True)
    industries: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    countries: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    companies: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    model: Mapped[str] = mapped_column(String(64))
    prompt_version: Mapped[str] = mapped_column(String(32))

    news_item: Mapped[NewsItem] = relationship(back_populates="classification")


class Summary(Base, UUIDPk, Timestamped):
    __tablename__ = "summaries"

    news_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("news_items.id", ondelete="CASCADE"), unique=True
    )
    thesis: Mapped[str] = mapped_column(Text)
    # structured points: [{text: str, citation_offsets: [int, int]}]
    supporting_points: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    implications: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    data_points: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    model: Mapped[str] = mapped_column(String(64))
    prompt_version: Mapped[str] = mapped_column(String(32))

    news_item: Mapped[NewsItem] = relationship(back_populates="summary")


class Report(Base, UUIDPk, Timestamped):
    __tablename__ = "reports"

    date: Mapped[date] = mapped_column(Date, index=True)
    type: Mapped[ReportType] = mapped_column(Enum(ReportType), index=True)
    body_md: Mapped[str] = mapped_column(Text)
    pdf_url: Mapped[str | None] = mapped_column(String(2048))
    version: Mapped[int] = mapped_column(Integer, default=1)
    prev_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id"), nullable=True
    )
    model: Mapped[str] = mapped_column(String(64))
    prompt_version: Mapped[str] = mapped_column(String(32))


class Embedding(Base, UUIDPk, Timestamped):
    __tablename__ = "embeddings"

    owner_table: Mapped[str] = mapped_column(String(64))
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text)
    vector: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dimensions))


class ProcessingJob(Base, UUIDPk, Timestamped):
    __tablename__ = "processing_jobs"

    news_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("news_items.id", ondelete="CASCADE")
    )
    step: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
