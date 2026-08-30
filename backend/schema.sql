-- SAM ICONIC Development Pvt Ltd - Supabase schema
-- Run this once in the Supabase dashboard: SQL Editor -> New query -> paste -> Run.

-- 1. Table for project metadata -------------------------------------------------
create table if not exists public.projects (
  id                uuid primary key default gen_random_uuid(),
  title             text        not null,
  description       text        not null,
  original_filename text        not null,
  storage_path      text        not null,
  size_bytes        bigint      not null,
  uploaded_at       timestamptz not null default now()
);

-- 2. Row Level Security --------------------------------------------------------
-- Public can READ the list. All writes go through the backend with the
-- service_role key, which bypasses RLS - so no insert/update/delete policy.
alter table public.projects enable row level security;

drop policy if exists "projects public read" on public.projects;
create policy "projects public read"
  on public.projects for select
  using (true);

-- 3. Storage bucket for the PDF files ----------------------------------------
insert into storage.buckets (id, name, public)
values ('project-pdfs', 'project-pdfs', true)
on conflict (id) do nothing;
