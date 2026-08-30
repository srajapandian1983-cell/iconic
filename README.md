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

- A **project** (`projects` table) has a title + description and **one or more files**.
- Each **file** (`project_files` table) is a PDF stored in the Supabase Storage
  bucket `project-pdfs` (public), under a folder named after the project id.
- The **public site** reads projects + their files with the *publishable* key (read-only).
  Each file opens in a full-size in-page PDF viewer.
- **admin.html** requires a Supabase login; only signed-in admins can create
  projects, **＋ Add file** to a project, or delete files / projects.

## First-time setup (once)

1. **Run the SQL:** Supabase dashboard → SQL Editor → paste [supabase-setup.sql](supabase-setup.sql) → Run.
2. **Create your admin login:** Supabase dashboard → Authentication → Users →
   Add user → *Create new user* → enter your email + a password, tick
   **Auto Confirm User**.

## Adding projects & files

1. Open **admin.html** (locally: double-click the file; or the live URL above).
2. Sign in with the email / password from the setup step.
3. **Add a new project:** title + description + first PDF → *Create project*.
4. **Add more files:** on any project in the list, click **＋ Add file** and pick a PDF.
5. Everything shows on the site under **Our Ongoing Projects**; each file opens
   in a large in-page viewer. Delete individual files or a whole project from admin.html.
