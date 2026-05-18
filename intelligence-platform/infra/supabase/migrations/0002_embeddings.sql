-- =============================================================
--  0002_embeddings — pgvector store + HNSW index.
--  Dimension matches OPENAI text-embedding-3-large (1536) by default.
--  Change `vector(1536)` if you swap providers.
-- =============================================================

create table if not exists embeddings (
  id              uuid primary key default gen_random_uuid(),
  owner_table     text not null,
  owner_id        uuid not null,
  chunk_index     int not null default 0,
  content         text not null,
  vector          vector(1536),
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index if not exists embeddings_owner_idx on embeddings (owner_table, owner_id);

-- HNSW gives us low-latency ANN; tune m / ef_construction for recall.
create index if not exists embeddings_vec_hnsw
  on embeddings using hnsw (vector vector_cosine_ops)
  with (m = 16, ef_construction = 64);
