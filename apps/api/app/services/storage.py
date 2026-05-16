"""Object-storage adapter — uniform interface over MinIO, Supabase Storage, S3, R2.

The PDF microservice and report builder call `put_pdf` / `get_pdf_url`
through this module; the concrete backend is selected by `STORAGE_BACKEND`.
"""

from __future__ import annotations

from typing import Protocol

import httpx
import structlog

from app.core.config import settings

log = structlog.get_logger()


class ObjectStorage(Protocol):
    async def put_pdf(self, key: str, content: bytes) -> str:
        """Upload bytes; return a stable URL or object key."""

    async def get_pdf_url(self, key: str) -> str:
        """Return a public (or signed) URL for the given key."""


# ---------- Supabase Storage ----------

class SupabaseStorage:
    """Supabase Storage (S3-compatible) — public bucket gives plain URLs."""

    def __init__(self) -> None:
        if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
            raise RuntimeError("SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY required for storage backend 'supabase'")
        self.base = settings.SUPABASE_URL.rstrip("/")
        self.bucket = settings.SUPABASE_STORAGE_BUCKET
        self._headers = {
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        }

    async def put_pdf(self, key: str, content: bytes) -> str:
        url = f"{self.base}/storage/v1/object/{self.bucket}/{key}"
        async with httpx.AsyncClient(timeout=60.0) as c:
            res = await c.post(
                url,
                headers={**self._headers, "Content-Type": "application/pdf", "x-upsert": "true"},
                content=content,
            )
            res.raise_for_status()
        log.info("storage.put_pdf.supabase", key=key, bytes=len(content))
        return key

    async def get_pdf_url(self, key: str) -> str:
        # Public bucket convention. If the bucket is private, swap for a signed URL.
        return f"{self.base}/storage/v1/object/public/{self.bucket}/{key}"


# ---------- MinIO / S3 / R2 ----------

class MinioStorage:
    """MinIO (and S3-compatible) backend. Used in dev + self-hosted prod."""

    def __init__(self) -> None:
        from minio import Minio

        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket = settings.MINIO_BUCKET
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    async def put_pdf(self, key: str, content: bytes) -> str:
        from io import BytesIO

        self.client.put_object(self.bucket, key, BytesIO(content), len(content), content_type="application/pdf")
        log.info("storage.put_pdf.minio", key=key, bytes=len(content))
        return key

    async def get_pdf_url(self, key: str) -> str:
        return self.client.presigned_get_object(self.bucket, key)


# ---------- Factory ----------

_singleton: ObjectStorage | None = None


def storage() -> ObjectStorage:
    global _singleton
    if _singleton is None:
        if settings.STORAGE_BACKEND == "supabase":
            _singleton = SupabaseStorage()
        else:
            _singleton = MinioStorage()
    return _singleton
