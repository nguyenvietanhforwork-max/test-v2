"""init schema — Atlas v0.1

Revision ID: 0001_init
Revises:
Create Date: 2026-05-15

Creates the full schema for the Atlas intelligence platform:
    users · industries · entities · news_items · news_industries · news_entities
    embeddings (pgvector) · reports · report_sections · report_sources
    pipeline_runs · pipeline_steps · pipeline_dead_letters · wiki_pages · audit_log

Plus required extensions: pgvector, pg_trgm (for trigram fuzzy search).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # ---------- Enums ----------
    region = postgresql.ENUM("VN", "INT", name="region", create_type=True)
    bucket = postgresql.ENUM("macro", "corp", name="bucket", create_type=True)
    confidence = postgresql.ENUM("low", "mid", "high", name="confidence", create_type=True)
    report_type = postgresql.ENUM("daily", "weekly", "master", "industry", "entity", name="reporttype", create_type=True)
    pipeline_status = postgresql.ENUM("queued", "running", "done", "failed", name="pipelinestatus", create_type=True)

    bind = op.get_bind()
    for e in (region, bucket, confidence, report_type, pipeline_status):
        e.create(bind, checkfirst=True)

    # ---------- Tables ----------
    op.create_table(
        "user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(256), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "industry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("color", sa.String(16)),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "entity",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(96), nullable=False, unique=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False, server_default="company"),
        sa.Column("ticker", sa.String(16)),
        sa.Column("exchange", sa.String(16)),
        sa.Column("country", sa.String(8)),
        sa.Column("aliases", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column("wiki_path", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_entity_ticker", "entity", ["ticker"])
    op.create_index("ix_entity_name_trgm", "entity", ["name"], postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"})

    op.create_table(
        "news_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("thesis", sa.Text(), nullable=False),
        sa.Column("bullets", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column("body_md", sa.Text(), nullable=False),
        sa.Column("url", sa.String(1024)),
        sa.Column("source_name", sa.String(128), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_path", sa.String(1024), nullable=False, unique=True),
        sa.Column("wiki_path", sa.String(1024)),
        sa.Column("content_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("region", region, nullable=False),
        sa.Column("bucket", bucket, nullable=False),
        sa.Column("confidence", confidence, nullable=False, server_default="mid"),
        sa.Column("sentiment", sa.Float()),
        sa.Column("archived", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("meta", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_news_published_at", "news_item", ["published_at"])
    op.create_index("ix_news_published_region_bucket", "news_item", ["published_at", "region", "bucket"])
    op.create_index("ix_news_title_trgm", "news_item", ["title"], postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"})

    op.create_table(
        "news_industry",
        sa.Column("news_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("news_item.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("industry_id", sa.Integer(), sa.ForeignKey("industry.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("relevance", sa.Float(), server_default="1.0", nullable=False),
    )

    op.create_table(
        "news_entity",
        sa.Column("news_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("news_item.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("entity.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("relevance", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("sentiment", sa.Float()),
    )

    op.create_table(
        "embedding",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("news_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("news_item.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("vector", Vector(3072), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    # HNSW index for fast ANN. Adjust m/ef_construction in prod.
    op.execute("CREATE INDEX ix_embedding_vector_hnsw ON embedding USING hnsw (vector vector_cosine_ops);")

    op.create_table(
        "report",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", report_type, nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("thesis", sa.Text(), nullable=False),
        sa.Column("markdown", sa.Text(), nullable=False),
        sa.Column("pdf_object_key", sa.String(512)),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True)),
        sa.Column("period_end", sa.DateTime(timezone=True)),
        sa.Column("meta", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_report_published_at", "report", ["published_at"])

    op.create_table(
        "report_section",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("report.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column("heading", sa.String(256), nullable=False),
        sa.Column("body_md", sa.Text(), nullable=False),
    )

    op.create_table(
        "report_source",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("section_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("report_section.id", ondelete="CASCADE"), nullable=False),
        sa.Column("news_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("news_item.id", ondelete="CASCADE"), nullable=False),
        sa.Column("citation_label", sa.String(64)),
        sa.UniqueConstraint("section_id", "news_id", name="uq_section_news"),
    )

    op.create_table(
        "pipeline_run",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("news_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("news_item.id", ondelete="SET NULL")),
        sa.Column("status", pipeline_status, nullable=False, server_default="queued"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("total_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_latency_ms", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "pipeline_step",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pipeline_run.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("status", pipeline_status, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("tokens", sa.Integer()),
        sa.Column("model", sa.String(64)),
        sa.Column("input_meta", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("output_meta", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("error", sa.Text()),
    )

    op.create_table(
        "pipeline_dead_letter",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pipeline_run.id", ondelete="SET NULL")),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("error", sa.Text(), nullable=False),
        sa.Column("traceback", sa.Text()),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "wiki_page",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("path", sa.String(1024), nullable=False, unique=True),
        sa.Column("title", sa.String(512)),
        sa.Column("kind", sa.String(32)),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("frontmatter", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target", sa.String(512), nullable=False),
        sa.Column("detail", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_audit_log_at", "audit_log", ["at"])


def downgrade() -> None:
    for t in [
        "audit_log", "wiki_page", "pipeline_dead_letter", "pipeline_step", "pipeline_run",
        "report_source", "report_section", "report",
        "embedding", "news_entity", "news_industry", "news_item",
        "entity", "industry", "user",
    ]:
        op.drop_table(t)
    for e in ["pipelinestatus", "reporttype", "confidence", "bucket", "region"]:
        op.execute(f"DROP TYPE IF EXISTS {e};")
