-- =============================================================
--  0001_init — core schema for the Intelligence Platform.
--  Idempotent where possible.
-- =============================================================

create extension if not exists "pgcrypto";
create extension if not exists "pg_trgm";
create extension if not exists "vector";

-- ----------------------- enums -------------------------------
do $$ begin
  create type bucket_t as enum ('vn_corp', 'intl_corp', 'vn_macro', 'intl_macro');
exception when duplicate_object then null; end $$;

do $$ begin
  create type news_status_t as enum (
    'queued', 'classified', 'summarized', 'reported', 'archived', 'failed'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type report_type_t as enum ('news', 'social', 'pdf', 'master');
exception when duplicate_object then null; end $$;

do $$ begin
  create type wiki_type_t as enum ('concept', 'entity', 'source-summary', 'comparison');
exception when duplicate_object then null; end $$;

do $$ begin
  create type entity_type_t as enum ('company', 'industry', 'country', 'person', 'theme');
exception when duplicate_object then null; end $$;

-- ----------------------- news_items --------------------------
create table if not exists news_items (
  id              uuid primary key default gen_random_uuid(),
  content_hash    text unique not null,
  vault_path      text not null,
  source_url      text,
  title           text not null,
  publish_date    date,
  language        text not null default 'vi',
  raw_text        text not null,
  status          news_status_t not null default 'queued',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index if not exists news_items_publish_date_idx on news_items (publish_date desc);
create index if not exists news_items_status_idx on news_items (status);

-- ----------------------- classifications ---------------------
create table if not exists classifications (
  id              uuid primary key default gen_random_uuid(),
  news_item_id    uuid unique not null references news_items(id) on delete cascade,
  bucket          bucket_t not null,
  industries      text[] not null default '{}',
  countries       text[] not null default '{}',
  companies       text[] not null default '{}',
  confidence      double precision not null default 0,
  model           text not null,
  prompt_version  text not null,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index if not exists classifications_bucket_idx on classifications (bucket);
create index if not exists classifications_industries_gin on classifications using gin (industries);
create index if not exists classifications_countries_gin on classifications using gin (countries);
create index if not exists classifications_companies_gin on classifications using gin (companies);

-- ----------------------- summaries ---------------------------
create table if not exists summaries (
  id                  uuid primary key default gen_random_uuid(),
  news_item_id        uuid unique not null references news_items(id) on delete cascade,
  thesis              text not null,
  supporting_points   jsonb not null default '[]',
  implications        jsonb not null default '[]',
  data_points         jsonb not null default '[]',
  model               text not null,
  prompt_version      text not null,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

-- ----------------------- reports -----------------------------
create table if not exists reports (
  id                  uuid primary key default gen_random_uuid(),
  date                date not null,
  type                report_type_t not null,
  body_md             text not null,
  pdf_url             text,
  version             int not null default 1,
  prev_version_id     uuid references reports(id),
  model               text not null,
  prompt_version      text not null,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);
create index if not exists reports_date_type_idx on reports (date desc, type);

-- ----------------------- wiki_pages --------------------------
create table if not exists wiki_pages (
  id              uuid primary key default gen_random_uuid(),
  slug            text unique not null,
  title           text not null,
  type            wiki_type_t not null,
  body_md         text not null,
  frontmatter     jsonb not null default '{}',
  vault_path      text not null,
  confidence      text not null default 'medium',
  manual_edit     boolean not null default false,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index if not exists wiki_pages_slug_trgm_idx on wiki_pages using gin (slug gin_trgm_ops);
create index if not exists wiki_pages_title_trgm_idx on wiki_pages using gin (title gin_trgm_ops);

-- ----------------------- entities ----------------------------
create table if not exists entities (
  id              uuid primary key default gen_random_uuid(),
  name            text not null,
  type            entity_type_t not null,
  aliases         text[] not null default '{}',
  ticker          text,
  country         text,
  industry        text,
  wiki_page_id    uuid references wiki_pages(id) on delete set null,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  unique (name, type)
);
create index if not exists entities_name_trgm_idx on entities using gin (name gin_trgm_ops);
create index if not exists entities_aliases_gin_idx on entities using gin (aliases);

-- ----------------------- linking -----------------------------
create table if not exists news_item_entities (
  news_item_id    uuid references news_items(id) on delete cascade,
  entity_id       uuid references entities(id) on delete cascade,
  relevance       double precision not null default 0.5,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  primary key (news_item_id, entity_id)
);

create table if not exists wiki_page_sources (
  wiki_page_id    uuid references wiki_pages(id) on delete cascade,
  news_item_id    uuid references news_items(id) on delete cascade,
  citation_text   text not null default '',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  primary key (wiki_page_id, news_item_id)
);

create table if not exists report_news_items (
  report_id       uuid references reports(id) on delete cascade,
  news_item_id    uuid references news_items(id) on delete cascade,
  ordinal         int not null default 0,
  primary key (report_id, news_item_id)
);

-- ----------------------- processing jobs ---------------------
create table if not exists processing_jobs (
  id              uuid primary key default gen_random_uuid(),
  news_item_id    uuid not null references news_items(id) on delete cascade,
  step            text not null,
  status          text not null default 'pending',
  attempts        int not null default 0,
  last_error      text,
  started_at      timestamptz,
  finished_at     timestamptz,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index if not exists processing_jobs_status_idx on processing_jobs (status);

-- ----------------------- audit log ---------------------------
create table if not exists audit_log (
  id              bigserial primary key,
  table_name      text not null,
  row_id          uuid,
  action          text not null,
  actor           text,
  diff            jsonb,
  created_at      timestamptz not null default now()
);
create index if not exists audit_log_table_row_idx on audit_log (table_name, row_id);

-- ----------------------- updated_at triggers -----------------
create or replace function set_updated_at() returns trigger as $$
begin new.updated_at = now(); return new; end; $$ language plpgsql;

do $$
declare t text;
begin
  for t in select unnest(array[
    'news_items','classifications','summaries','reports','wiki_pages',
    'entities','news_item_entities','wiki_page_sources','processing_jobs'
  ]) loop
    execute format($f$
      drop trigger if exists trg_set_updated_at on %1$I;
      create trigger trg_set_updated_at before update on %1$I
        for each row execute function set_updated_at();
    $f$, t);
  end loop;
end $$;
