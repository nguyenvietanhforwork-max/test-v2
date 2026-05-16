-- =============================================================
--  0004_storage — create the storage bucket for generated PDFs.
--  Run via Supabase dashboard or `supabase storage` CLI; included
--  here for documentation / replay.
-- =============================================================

-- The Supabase storage extension exposes `storage.buckets` and
-- `storage.objects`. We only create the bucket; access is controlled
-- via storage policies in the Supabase dashboard.
insert into storage.buckets (id, name, public)
values ('reports', 'reports', false)
on conflict (id) do nothing;
