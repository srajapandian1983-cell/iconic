-- SAM ICONIC Development Pvt Ltd - Supabase setup
-- Run once in the Supabase dashboard: SQL Editor -> New query -> paste all -> Run.
-- Safe to run again (idempotent).

-- 1. Projects (title + description) -------------------------------------------
create table if not exists public.projects (
  id          uuid primary key default gen_random_uuid(),
  title       text        not null,
  description text        not null,
  uploaded_at timestamptz not null default now()
);

alter table public.projects enable row level security;

drop policy if exists "projects public read" on public.projects;
create policy "projects public read" on public.projects
  for select using (true);

drop policy if exists "projects auth insert" on public.projects;
create policy "projects auth insert" on public.projects
  for insert to authenticated with check (true);

drop policy if exists "projects auth delete" on public.projects;
create policy "projects auth delete" on public.projects
  for delete to authenticated using (true);

-- These columns existed in an earlier single-file version; keep them optional.
alter table public.projects alter column original_filename drop not null;
alter table public.projects alter column storage_path      drop not null;
alter table public.projects alter column size_bytes        drop not null;

-- 2. Files that belong to a project (many per project) ---------------------
create table if not exists public.project_files (
  id                uuid primary key default gen_random_uuid(),
  project_id        uuid not null references public.projects(id) on delete cascade,
  original_filename text        not null,
  storage_path      text        not null,
  size_bytes        bigint      not null,
  uploaded_at       timestamptz not null default now()
);
create index if not exists project_files_project_id_idx
  on public.project_files(project_id);

alter table public.project_files enable row level security;

drop policy if exists "project_files public read" on public.project_files;
create policy "project_files public read" on public.project_files
  for select using (true);

drop policy if exists "project_files auth insert" on public.project_files;
create policy "project_files auth insert" on public.project_files
  for insert to authenticated with check (true);

drop policy if exists "project_files auth delete" on public.project_files;
create policy "project_files auth delete" on public.project_files
  for delete to authenticated using (true);

-- Move any existing single-file-per-project data into project_files.
insert into public.project_files (project_id, original_filename, storage_path, size_bytes, uploaded_at)
select p.id, p.original_filename, p.storage_path, p.size_bytes, p.uploaded_at
from public.projects p
where p.storage_path is not null
  and not exists (select 1 from public.project_files f where f.storage_path = p.storage_path);

-- 2b. Contact / enquiry requests from the website ------------------------
create table if not exists public.enquiries (
  id         uuid primary key default gen_random_uuid(),
  name       text not null,
  phone      text not null,
  email      text,
  message    text not null,
  created_at timestamptz not null default now()
);

alter table public.enquiries enable row level security;

-- anyone can submit the contact form
drop policy if exists "enquiries public insert" on public.enquiries;
create policy "enquiries public insert" on public.enquiries
  for insert to anon, authenticated with check (true);

-- only signed-in admins can read / delete them
drop policy if exists "enquiries auth read" on public.enquiries;
create policy "enquiries auth read" on public.enquiries
  for select to authenticated using (true);

drop policy if exists "enquiries auth delete" on public.enquiries;
create policy "enquiries auth delete" on public.enquiries
  for delete to authenticated using (true);

-- 2c. Team members shown on the website "Our Team" section ---------------
create table if not exists public.team_members (
  id         uuid primary key default gen_random_uuid(),
  name       text not null,
  position   text not null,
  photo_path text,
  sort_order int  not null default 0,
  created_at timestamptz not null default now()
);

alter table public.team_members enable row level security;

drop policy if exists "team public read" on public.team_members;
create policy "team public read" on public.team_members
  for select using (true);

drop policy if exists "team auth insert" on public.team_members;
create policy "team auth insert" on public.team_members
  for insert to authenticated with check (true);

drop policy if exists "team auth delete" on public.team_members;
create policy "team auth delete" on public.team_members
  for delete to authenticated using (true);

-- Team photos are stored in the same 'project-pdfs' bucket, under team/.

-- 3. Storage bucket for the files ---------------------------------------
insert into storage.buckets (id, name, public, file_size_limit)
values ('project-pdfs', 'project-pdfs', true, 52428800)   -- 50 MB
on conflict (id) do nothing;

-- Set the limit on an already-created bucket:
update storage.buckets set file_size_limit = 52428800 where id = 'project-pdfs';
-- The Dashboard -> Storage -> Settings "Upload file size limit" (free plan
-- default 50 MB) is the project-wide cap; keep it at 50 MB.

-- Storage policies (INSERT/DELETE for signed-in admins) must be added in the
-- dashboard: Storage -> Policies -> New policy -> For full customization
--   name: pdfs auth upload   operation: INSERT   role: authenticated
--   WITH CHECK:  bucket_id = 'project-pdfs'
--   name: pdfs auth delete   operation: DELETE   role: authenticated
--   USING:       bucket_id = 'project-pdfs'
-- (public read is automatic for a public bucket)

-- 4. Admin login: Authentication -> Users -> Add user -> Create new user
--    enter email + password, tick "Auto Confirm User". Sign in at <site>/admin.html
