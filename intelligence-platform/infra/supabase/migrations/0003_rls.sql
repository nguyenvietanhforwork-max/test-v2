-- =============================================================
--  0003_rls — Row Level Security.
--  service_role bypasses; authenticated users get read-only.
--  Anon has no access.
-- =============================================================

do $$
declare t text;
begin
  for t in select unnest(array[
    'news_items','classifications','summaries','reports','wiki_pages',
    'entities','news_item_entities','wiki_page_sources','report_news_items',
    'processing_jobs','embeddings','audit_log'
  ]) loop
    execute format('alter table %I enable row level security;', t);
  end loop;
end $$;

-- read-only for authenticated
do $$
declare t text;
begin
  for t in select unnest(array[
    'news_items','classifications','summaries','reports','wiki_pages',
    'entities','news_item_entities','wiki_page_sources','report_news_items'
  ]) loop
    execute format($f$
      drop policy if exists auth_read on %1$I;
      create policy auth_read on %1$I
        for select to authenticated using (true);
    $f$, t);
  end loop;
end $$;

-- service_role implicit bypass (Supabase grants it bypassrls)
