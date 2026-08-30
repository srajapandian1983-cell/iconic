# SAM ICONIC Development Pvt Ltd - Project Upload Backend

Backend API to upload real estate project files as **PDF** with a **description**.
Storage is **Supabase**:

- file metadata -> Postgres table `public.projects`
- the PDF files -> Storage bucket `project-pdfs` (public)

## Company

- SAM ICONIC Development Private Limited
- 195/28, Gandhi Road, West Tambaram, Chennai 600045
- Phone: 6385106308

## One-time Supabase setup

1. Open the Supabase dashboard for project `mmmyliccvuawhyhcxusw`.
2. **SQL Editor -> New query**, paste the contents of [schema.sql](schema.sql), **Run**.
   This creates the `projects` table, its read policy, and the `project-pdfs` bucket.
3. **Project Settings -> API**, copy the **`service_role`** key.

## Local setup

```powershell
cd "d:\Moonvera\Iconic site\backend"
python -m pip install -r requirements.txt
copy .env.example .env
# edit .env and paste SUPABASE_SERVICE_ROLE_KEY
python app.py
```

Server runs at `http://127.0.0.1:5000/`.

## Uploading a project

**Easiest:** double-click **`START-UPLOAD.bat`** in this folder. It starts the
server and opens the upload page automatically. Keep that window open while
uploading; close it when done.

Or manually: run `python app.py`, then open **`http://127.0.0.1:5000/upload`**.

On the page: pick the PDF, type a title and description, click **Upload**. The
same page lists every uploaded project with a **View PDF** link and a
**Delete** button.

Uploaded projects appear automatically in the "Our Ongoing Projects" section
of the public website.

## Environment (`backend/.env`)

| Variable | Default | Meaning |
|----------|---------|---------|
| `SUPABASE_URL` | `https://mmmyliccvuawhyhcxusw.supabase.co` | Project API URL |
| `SUPABASE_SERVICE_ROLE_KEY` | *(required)* | Secret server key - never expose to the browser |
| `SUPABASE_BUCKET` | `project-pdfs` | Storage bucket name |
| `MAX_CONTENT_MB` | `25` | Max upload size in MB |
| `PORT` | `5000` | Port to run on |

`.env` is git-ignored. Rotate the key any time in Supabase settings.

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | API + company info |
| GET | `/upload` | Browser upload form + project list |
| GET | `/api/projects` | List all uploaded projects (newest first) |
| GET | `/api/projects/<id>` | One project's details |
| POST | `/api/projects` | Upload a project (see below) |
| GET | `/api/projects/<id>/file` | Redirects to the public PDF URL |
| DELETE | `/api/projects/<id>` | Remove a project (row + file) |

### Upload

`POST /api/projects` as `multipart/form-data`:

| Field | Required | Notes |
|-------|----------|-------|
| `pdf` | yes | Must be a real PDF (`.pdf` + `%PDF-` header). |
| `description` | yes | Text description of the project. |
| `title` | no | Defaults to the file name without `.pdf`. |

Max file size: 25 MB (`MAX_CONTENT_MB`).

### Example (PowerShell)

```powershell
curl.exe -F "pdf=@C:\path\to\project.pdf" -F "description=Residential plots at West Tambaram" http://127.0.0.1:5000/api/projects
```

### Example response

```json
{
  "id": "3f9c1e2a-...",
  "title": "project",
  "description": "Residential plots at West Tambaram",
  "original_filename": "project.pdf",
  "size_bytes": 184213,
  "uploaded_at": "2026-08-30T10:15:00+00:00",
  "file_url": "https://mmmyliccvuawhyhcxusw.supabase.co/storage/v1/object/public/project-pdfs/3f9c1e2a-....pdf"
}
```
