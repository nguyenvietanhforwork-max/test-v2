"""Wiki + entity ORM models."""

import enum
import uuid

from sqlalchemy import ARRAY, Enum, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Timestamped, UUIDPk


class WikiType(str, enum.Enum):
    concept = "concept"
    entity = "entity"
    source_summary = "source-summary"
    comparison = "comparison"


class EntityType(str, enum.Enum):
    company = "company"
    industry = "industry"
    country = "country"
    person = "person"
    theme = "theme"


class WikiPage(Base, UUIDPk, Timestamped):
    __tablename__ = "wiki_pages"

    slug: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512))
    type: Mapped[WikiType] = mapped_column(Enum(WikiType))
    body_md: Mapped[str] = mapped_column(Text)
    frontmatter: Mapped[dict] = mapped_column(JSONB, default=dict)
    vault_path: Mapped[str] = mapped_column(String(1024))
    confidence: Mapped[str] = mapped_column(String(16), default="medium")  # high|medium|low


class Entity(Base, UUIDPk, Timestamped):
    __tablename__ = "entities"

    name: Mapped[str] = mapped_column(String(512), index=True)
    type: Mapped[EntityType] = mapped_column(Enum(EntityType), index=True)
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    ticker: Mapped[str | None] = mapped_column(String(16))
    country: Mapped[str | None] = mapped_column(String(8))
    industry: Mapped[str | None] = mapped_column(String(128))
    wiki_page_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wiki_pages.id", ondelete="SET NULL")
    )

    __table_args__ = (UniqueConstraint("name", "type", name="uq_entity_name_type"),)


class NewsItemEntity(Base, Timestamped):
    __tablename__ = "news_item_entities"

    news_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("news_items.id", ondelete="CASCADE"), primary_key=True
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True
    )
    relevance: Mapped[float] = mapped_column(Float, default=0.5)


class WikiPageSource(Base, Timestamped):
    __tablename__ = "wiki_page_sources"

    wiki_page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wiki_pages.id", ondelete="CASCADE"), primary_key=True
    )
    news_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("news_items.id", ondelete="CASCADE"), primary_key=True
    )
    citation_text: Mapped[str] = mapped_column(Text)
