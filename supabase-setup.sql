-- SAM ICONIC Development Pvt Ltd - Supabase setup
-- Run once in the Supabase dashboard: SQL Editor -> New query -> paste all -> Run.
-- Safe to run again (idempotent).

-- 1. Table for project metadata ---------------------------------------------
create table if not exists public.projects (
  id                uuid primary key default gen_random_uuid(),
  title             text        not null,
  description       text        not null,
  original_filename text        not null,
  storage_path      text        not null,
  size_bytes        bigint      not null,
  uploaded_at       timestamptz not null default now()
);

alter table public.projects enable row level security;

-- Everyone can read the project list (used by the public website).
drop policy if exists "projects public read" on public.projects;
create policy "projects public read"
  on public.projects for select
  using (true);

-- Only signed-in admins (admin.html login) can add / remove projects.
drop policy if exists "projects auth insert" on public.projects;
create policy "projects auth insert"
  on public.projects for insert to authenticated
  with check (true);

drop policy if exists "projects auth delete" on public.projects;
create policy "projects auth delete"
  on public.projects for delete to authenticated
  using (true);

-- 2. Storage bucket for the PDF files -------------------------------------
insert into storage.buckets (id, name, public)
values ('project-pdfs', 'project-pdfs', true)
on conflict (id) do nothing;

-- Public read is automatic for a public bucket.
-- Signed-in admins can upload and delete objects in this bucket.
drop policy if exists "pdfs auth upload" on storage.objects;
create policy "pdfs auth upload"
  on storage.objects for insert to authenticated
  with check (bucket_id = 'project-pdfs');

drop policy if exists "pdfs auth delete" on storage.objects;
create policy "pdfs auth delete"
  on storage.objects for delete to authenticated
  using (bucket_id = 'project-pdfs');

-- 3. Create the admin login -------------------------------------------------
-- Do this in the dashboard, not SQL:
--   Authentication -> Users -> Add user -> Create new user
--   - enter your email + a password
--   - tick "Auto Confirm User"
-- Then sign in at  <site>/admin.html
