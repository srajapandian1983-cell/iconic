# SAM ICONIC Development Pvt Ltd — Real Estate

Static website for **SAM ICONIC Development Private Limited**. No server to run —
just HTML + Supabase.

- 195/28, Gandhi Road, West Tambaram, Chennai 600045
- Phone: 6385106308

**Live site:** https://srajapandian1983-cell.github.io/iconic/
**Admin (upload):** https://srajapandian1983-cell.github.io/iconic/admin.html

## Files

| Path | What it is |
|------|-----------|
| [index.html](index.html) | The public website. Reads the "Our Ongoing Projects" list from Supabase. |
| [admin.html](admin.html) | Password-protected upload page. Sign in, then add / delete project PDFs. |
| [supabase-setup.sql](supabase-setup.sql) | One-time Supabase setup (table, security rules, storage bucket). |

## How it works

- **Metadata** (title, description, …) lives in a Supabase Postgres table `projects`.
- **PDF files** live in a Supabase Storage bucket `project-pdfs` (public).
- The **public site** reads the list with the *publishable* key (read-only).
- **admin.html** requires a Supabase login; only signed-in admins can upload / delete.

## First-time setup (once)

1. **Run the SQL:** Supabase dashboard → SQL Editor → paste [supabase-setup.sql](supabase-setup.sql) → Run.
2. **Create your admin login:** Supabase dashboard → Authentication → Users →
   Add user → *Create new user* → enter your email + a password, tick
   **Auto Confirm User**.

## Adding a project

1. Open **admin.html** (locally: double-click the file; or the live URL above).
2. Sign in with the email / password from step 2 above.
3. Pick the PDF, type a title + description, click **Upload**.
4. It appears on the site under **Our Ongoing Projects**. Delete from the same page.
