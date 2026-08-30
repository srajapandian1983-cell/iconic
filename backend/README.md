# SAM ICONIC Development Pvt Ltd - Project Upload Backend

Basic backend API to upload real estate project files as **PDF** with a
**description**. Files are stored on disk; metadata is kept in a JSON file.
No database or login yet - built to be upgraded step by step.

## Company

- SAM ICONIC Development Private Limited
- 195/28, Gandhi Road, West Tambaram, Chennai 600045
- Phone: 6385106308

## Setup

```powershell
cd "d:\Moonvera\Iconic site\backend"
python -m pip install -r requirements.txt
python app.py
```

Server runs at `http://127.0.0.1:5000/`.

## Folders (created automatically)

- `uploads/` - the stored PDF files
- `data/projects.json` - the metadata for each upload

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | API + company info |
| GET | `/api/projects` | List all uploaded projects (newest first) |
| GET | `/api/projects/<id>` | One project's details |
| POST | `/api/projects` | Upload a project (see below) |
| GET | `/api/projects/<id>/file` | Open / download the PDF |
| DELETE | `/api/projects/<id>` | Remove a project and its file |

### Upload

`POST /api/projects` as `multipart/form-data`:

| Field | Required | Notes |
|-------|----------|-------|
| `pdf` | yes | The file. Must be a real PDF (`.pdf` + `%PDF-` header). |
| `description` | yes | Text description of the project. |
| `title` | no | Defaults to the file name without `.pdf`. |

Max file size: 25 MB (change with the `MAX_CONTENT_MB` environment variable).

### Example (PowerShell)

```powershell
curl.exe -F "pdf=@C:\path\to\project.pdf" -F "description=Residential plots at West Tambaram" http://127.0.0.1:5000/api/projects
```

### Example response

```json
{
  "id": "3f9c1e2a...",
  "title": "project",
  "description": "Residential plots at West Tambaram",
  "original_filename": "project.pdf",
  "size_bytes": 184213,
  "uploaded_at": "2026-08-30T10:15:00+00:00",
  "file_url": "/api/projects/3f9c1e2a.../file"
}
```

## Environment variables (optional)

| Variable | Default | Meaning |
|----------|---------|---------|
| `PORT` | `5000` | Port to run on |
| `UPLOAD_DIR` | `backend/uploads` | Where PDFs are saved |
| `DATA_FILE` | `backend/data/projects.json` | Metadata file path |
| `MAX_CONTENT_MB` | `25` | Max upload size in MB |
