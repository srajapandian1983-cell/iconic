"""
SAM ICONIC Development Private Limited - Real Estate
Backend API : upload project brochures / documents as PDF with a description.

Storage is Supabase:
  - file metadata  -> Postgres table  public.projects
  - the PDF files   -> Storage bucket  project-pdfs   (public)

Setup:
    pip install -r requirements.txt
    # 1. run schema.sql once in the Supabase SQL editor
    # 2. copy .env.example -> .env and fill SUPABASE_SERVICE_ROLE_KEY
    python app.py

Then open http://127.0.0.1:5000/
"""

import os
import uuid
import re

from dotenv import load_dotenv
from flask import Flask, jsonify, request, redirect, abort
from werkzeug.utils import secure_filename
from supabase import create_client, Client

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
BUCKET = os.environ.get("SUPABASE_BUCKET", "project-pdfs")
MAX_CONTENT_MB = int(os.environ.get("MAX_CONTENT_MB", "25"))
TABLE = "projects"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise SystemExit(
        "Missing Supabase config. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
        "in backend/.env (see .env.example)."
    )

COMPANY = {
    "name": "SAM ICONIC Development Private Limited",
    "address": "195/28, Gandhi Road, West Tambaram, Chennai 600045",
    "phone": "6385106308",
}

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_MB * 1024 * 1024


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def is_pdf(file_storage):
    """Check extension and the %PDF- magic bytes at the start of the file."""
    name = (file_storage.filename or "").lower()
    if not name.endswith(".pdf"):
        return False
    head = file_storage.stream.read(5)
    file_storage.stream.seek(0)
    return head == b"%PDF-"


def public_url(storage_path):
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{storage_path}"


def public_record(row):
    """Shape a table row for the API response."""
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "original_filename": row["original_filename"],
        "size_bytes": row["size_bytes"],
        "uploaded_at": row["uploaded_at"],
        "file_url": public_url(row["storage_path"]),
    }


@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.get("/")
def index():
    return jsonify(
        {
            "company": COMPANY,
            "service": "Real estate project upload API (Supabase)",
            "storage": {"table": TABLE, "bucket": BUCKET},
            "endpoints": {
                "list_projects": "GET /api/projects",
                "get_project": "GET /api/projects/<id>",
                "upload_project": "POST /api/projects  (multipart form: pdf, description, title?)",
                "download_pdf": "GET /api/projects/<id>/file",
                "delete_project": "DELETE /api/projects/<id>",
            },
        }
    )


@app.get("/api/projects")
def list_projects():
    res = (
        supabase.table(TABLE)
        .select("*")
        .order("uploaded_at", desc=True)
        .execute()
    )
    return jsonify([public_record(r) for r in res.data])


@app.get("/api/projects/<pid>")
def get_project(pid):
    res = supabase.table(TABLE).select("*").eq("id", pid).limit(1).execute()
    if not res.data:
        abort(404, description="Project not found")
    return jsonify(public_record(res.data[0]))


@app.post("/api/projects")
def upload_project():
    if "pdf" not in request.files or request.files["pdf"].filename == "":
        abort(400, description="A PDF file is required in the 'pdf' field")

    pdf = request.files["pdf"]
    description = (request.form.get("description") or "").strip()
    title = (request.form.get("title") or "").strip()

    if not description:
        abort(400, description="A 'description' is required")
    if not is_pdf(pdf):
        abort(400, description="Only PDF files are accepted")

    original = secure_filename(pdf.filename) or "project.pdf"
    if not title:
        title = re.sub(r"\.pdf$", "", original, flags=re.IGNORECASE)

    pid = str(uuid.uuid4())
    storage_path = f"{pid}.pdf"
    data = pdf.read()

    try:
        supabase.storage.from_(BUCKET).upload(
            storage_path,
            data,
            {"content-type": "application/pdf", "upsert": "true"},
        )
    except Exception as exc:  # noqa: BLE001
        abort(502, description=f"Storage upload failed: {exc}")

    row = {
        "id": pid,
        "title": title,
        "description": description,
        "original_filename": original,
        "storage_path": storage_path,
        "size_bytes": len(data),
    }

    try:
        res = supabase.table(TABLE).insert(row).execute()
    except Exception as exc:  # noqa: BLE001
        supabase.storage.from_(BUCKET).remove([storage_path])
        abort(502, description=f"Database insert failed: {exc}")

    return jsonify(public_record(res.data[0])), 201


@app.get("/api/projects/<pid>/file")
def download_file(pid):
    res = supabase.table(TABLE).select("storage_path").eq("id", pid).limit(1).execute()
    if not res.data:
        abort(404, description="Project not found")
    return redirect(public_url(res.data[0]["storage_path"]), code=302)


@app.delete("/api/projects/<pid>")
def delete_project(pid):
    res = supabase.table(TABLE).select("storage_path").eq("id", pid).limit(1).execute()
    if not res.data:
        abort(404, description="Project not found")

    supabase.storage.from_(BUCKET).remove([res.data[0]["storage_path"]])
    supabase.table(TABLE).delete().eq("id", pid).execute()
    return jsonify({"deleted": pid})


# --------------------------------------------------------------------------
# Error handling -> always JSON
# --------------------------------------------------------------------------
@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(413)
@app.errorhandler(502)
def json_error(err):
    code = getattr(err, "code", 500)
    msg = getattr(err, "description", str(err))
    if code == 413:
        msg = f"File too large. Limit is {MAX_CONTENT_MB} MB."
    return jsonify({"error": msg, "status": code}), code


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)
