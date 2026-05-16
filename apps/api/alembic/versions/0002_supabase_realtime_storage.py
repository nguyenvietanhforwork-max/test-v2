"""supabase realtime, grants and storage hardening

Revision ID: 0002_supabase_realtime_storage
Revises: 0001_init
Create Date: 2026-05-16
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002_supabase_realtime_storage"
down_revision: Union[str, None] = "0001_init"
branch_labels = None
depends_on = None


READ_TABLES = [
    "industry",
    "entity",
    "news_item",
    "news_industry",
    "news_entity",
    "report",
    "report_section",
    "report_source",
    "wiki_page",
]

REALTIME_TABLES = [
    "news_item",
    "report",
    "pipeline_run",
    "pipeline_step",
]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    for table in READ_TABLES:
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"GRANT SELECT ON TABLE public.{table} TO anon, authenticated;")
        op.execute(
            f"""
            DO $$
            BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE schemaname = 'public'
                  AND tablename = '{table}'
                  AND policyname = '{table}_read_public'
              ) THEN
                CREATE POLICY {table}_read_public
                ON public.{table}
                FOR SELECT
                TO anon, authenticated
                USING (true);
              END IF;
            END $$;
            """
        )

    for table in REALTIME_TABLES:
        op.execute(
            f"""
            DO $$
            BEGIN
              IF EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime')
                 AND NOT EXISTS (
                   SELECT 1 FROM pg_publication_tables
                   WHERE pubname = 'supabase_realtime'
                     AND schemaname = 'public'
                     AND tablename = '{table}'
                 ) THEN
                ALTER PUBLICATION supabase_realtime ADD TABLE public.{table};
              END IF;
            END $$;
            """
        )

    op.execute(
        """
        DO $$
        BEGIN
          IF to_regclass('storage.buckets') IS NOT NULL THEN
            INSERT INTO storage.buckets (id, name, public)
            VALUES ('atlas-pdfs', 'atlas-pdfs', true)
            ON CONFLICT (id) DO UPDATE SET public = excluded.public;
          END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          IF to_regclass('storage.objects') IS NOT NULL THEN
            IF NOT EXISTS (
              SELECT 1 FROM pg_policies
              WHERE schemaname = 'storage'
                AND tablename = 'objects'
                AND policyname = 'atlas_pdfs_public_read'
            ) THEN
              CREATE POLICY atlas_pdfs_public_read
              ON storage.objects
              FOR SELECT
              TO anon, authenticated
              USING (bucket_id = 'atlas-pdfs');
            END IF;
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    for table in READ_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_read_public ON public.{table};")
    op.execute("DROP POLICY IF EXISTS atlas_pdfs_public_read ON storage.objects;")
