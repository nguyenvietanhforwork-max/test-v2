"""Centralized settings — env-driven via pydantic-settings.

Supabase-aware: if `SUPABASE_DB_URL` is set it takes precedence over the
discrete POSTGRES_* vars. Supabase ships pgvector + pg_trgm, so the Alembic
init migration works as-is.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Runtime
    ENV: Literal["dev", "staging", "prod"] = "dev"
    LOG_LEVEL: str = "info"
    DEBUG: bool = False

    # Vault
    VAULT_RAW: Path = Path("/vault/raw")
    VAULT_WIKI: Path = Path("/vault/wiki")
    VAULT_PROCESSED: Path = Path("/vault/Processed")

    # ---------- Database ----------
    # Preferred in prod: paste Supabase connection string directly.
    # Example: postgresql://postgres.<ref>:<pw>@aws-0-<region>.pooler.supabase.com:6543/postgres
    SUPABASE_DB_URL: str | None = None

    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "atlas"
    POSTGRES_PASSWORD: str = "atlas"
    POSTGRES_DB: str = "atlas"

    @property
    def DATABASE_URL(self) -> str:
        if self.SUPABASE_DB_URL:
            # Supabase gives `postgresql://...`; sync driver = psycopg3.
            url = self.SUPABASE_DB_URL
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            return url
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        # asyncpg for read-heavy + WebSocket workloads.
        return self.DATABASE_URL.replace("postgresql+psycopg", "postgresql+asyncpg")

    # ---------- Supabase (optional, for Storage + Realtime + Auth) ----------
    SUPABASE_URL: str | None = None              # https://<ref>.supabase.co
    SUPABASE_ANON_KEY: str | None = None         # public, safe to ship to frontend
    SUPABASE_PUBLISHABLE_KEY: str | None = None  # newer public key naming
    SUPABASE_SERVICE_ROLE_KEY: str | None = None # server-only — bypasses RLS
    SUPABASE_SECRET_KEY: str | None = None       # newer secret key naming

    def model_post_init(self, __context: object) -> None:
        if not self.SUPABASE_ANON_KEY and self.SUPABASE_PUBLISHABLE_KEY:
            self.SUPABASE_ANON_KEY = self.SUPABASE_PUBLISHABLE_KEY
        if not self.SUPABASE_SERVICE_ROLE_KEY and self.SUPABASE_SECRET_KEY:
            self.SUPABASE_SERVICE_ROLE_KEY = self.SUPABASE_SECRET_KEY

    # ---------- Redis ----------
    # Optional once Supabase Realtime is wired up (see services/realtime.py).
    REDIS_URL: str = "redis://redis:6379/0"
    USE_SUPABASE_REALTIME: bool = False   # if true, skip Redis pub/sub for FE fanout

    # ---------- Meilisearch ----------
    MEILI_HOST: str = "http://meili:7700"
    MEILI_MASTER_KEY: str = "change-me"

    # ---------- Object storage (PDFs) ----------
    # Modes: "minio" (self-hosted), "supabase" (Supabase Storage), "s3" (AWS), "r2" (Cloudflare)
    STORAGE_BACKEND: Literal["minio", "supabase", "s3", "r2"] = "minio"
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minio"
    MINIO_SECRET_KEY: str = "minio12345"
    MINIO_BUCKET: str = "atlas-pdfs"
    MINIO_SECURE: bool = False
    SUPABASE_STORAGE_BUCKET: str = "atlas-pdfs"

    # ---------- LLM ----------
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DEFAULT_MODEL: str = "claude-sonnet-4-6"
    FALLBACK_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIM: int = 3072

    # ---------- Auth ----------
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TTL: int = 3600
    JWT_REFRESH_TTL: int = 2_592_000

    # ---------- CORS ----------
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "https://atlas.vercel.app",
        ]
    )

    # ---------- Rate limit ----------
    RATE_LIMIT_RPM: int = 60

    # ---------- PDF microservice ----------
    PDF_SERVICE_URL: str = "http://pdf:4000"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
