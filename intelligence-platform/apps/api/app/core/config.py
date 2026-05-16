"""Typed settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # core
    env: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"

    # db
    database_url: str = Field(..., description="async asyncpg URL")
    database_url_sync: str = Field(..., description="sync URL for alembic")

    # supabase
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_jwt_secret: str | None = None

    # redis / celery
    redis_url: str
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    # ai
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    embedding_model: str = "text-embedding-3-large"
    embedding_dimensions: int = 1536
    summarization_model: str = "claude-sonnet-4-6"
    classification_model: str = "claude-haiku-4-5-20251001"
    report_model: str = "claude-opus-4-6"

    # n8n
    n8n_webhook_url: str | None = None
    n8n_api_key: str | None = None

    # vault
    vault_path: str = "/data/vault"
    vault_raw_dir: str = "raw"
    vault_wiki_dir: str = "wiki"
    vault_processed_dir: str = "Processed"
    vault_archive_dir: str = "raw/old news"

    # services
    api_base_url: str = "http://api:8000"
    agents_base_url: str = "http://agents:8001"
    pdf_engine_url: str = "http://pdf-engine:4000"
    dashboard_url: str = "http://localhost:3000"

    # search
    meilisearch_host: str | None = None
    meilisearch_master_key: str | None = None

    # cors
    cors_origins: list[str] = ["http://localhost:3000", "https://*.vercel.app"]

    # observability
    sentry_dsn: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
