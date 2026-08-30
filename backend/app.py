"""
SAM ICONIC Development Private Limited - Real Estate
Backend API : upload project brochures / documents as PDF with a description.

Basic pattern only. Stores files on disk and metadata in a JSON file.
No database, no auth yet - meant to be upgraded step by step.

Run:
    pip install -r requirements.txt
    python app.py

Then open http://127.0.0.1:5000/
"""

import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_from_directory, abort
from werkzeug.utils import secure_filename

# --------------------------------------------------------------------------
# Configuration (override with environment variables)
# --------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
DATA_FILE = os.environ.get("DATA_FILE", os.path.join(BASE_DIR, "data", "projects.json"))
MAX_CONTENT_MB = int(os.environ.get("MAX_CONTENT_MB", "25"))

COMPANY = {
    "name": "SAM ICONIC Development Private Limited",
    "address": "195/28, Gandhi Road, West Tambaram, Chennai 600045",
    "phone": "6385106308",
}

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_MB * 1024 * 1024

# One lock so concurrent uploads do not corrupt the JSON metadata file.
_lock = threading.Lock()


# --------------------------------------------------------------------------
# Metadata store (simple JSON file)
# --------------------------------------------------------------------------
def _read_all():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError:
            return []


def _write_all(records):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, DATA_FILE)


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


def public_record(rec):
    """Shape a stored record for the API response."""
    return {
        "id": rec["id"],
        "title": rec["title"],
        "description": rec["description"],
        "original_filename": rec["original_filename"],
        "size_bytes": rec["size_bytes"],
        "uploaded_at": rec["uploaded_at"],
        "file_url": f"/api/projects/{rec['id']}/file",
    }


@app.after_request
def add_cors(resp):
    # Allow the static site (index.html) to call this API from the browser.
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
            "service": "Real estate project upload API",
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
    records = sorted(_read_all(), key=lambda r: r["uploaded_at"], reverse=True)
    return jsonify([public_record(r) for r in records])


@app.get("/api/projects/<pid>")
def get_project(pid):
    for rec in _read_all():
        if rec["id"] == pid:
            return jsonify(public_record(rec))
    abort(404, description="Project not found")


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

    pid = uuid.uuid4().hex
    stored_name = f"{pid}.pdf"
    pdf.save(os.path.join(UPLOAD_DIR, stored_name))
    size_bytes = os.path.getsize(os.path.join(UPLOAD_DIR, stored_name))

    record = {
        "id": pid,
        "title": title,
        "description": description,
        "original_filename": original,
        "stored_filename": stored_name,
        "size_bytes": size_bytes,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }

    with _lock:
        records = _read_all()
        records.append(record)
        _write_all(records)

    return jsonify(public_record(record)), 201


@app.get("/api/projects/<pid>/file")
def download_file(pid):
    for rec in _read_all():
        if rec["id"] == pid:
            return send_from_directory(
                UPLOAD_DIR,
                rec["stored_filename"],
                mimetype="application/pdf",
                as_attachment=False,
                download_name=rec["original_filename"],
            )
    abort(404, description="Project not found")


@app.delete("/api/projects/<pid>")
def delete_project(pid):
    with _lock:
        records = _read_all()
        keep = [rec for rec in records if rec["id"] != pid]
        removed = next((rec for rec in records if rec["id"] == pid), None)
        if removed is None:
            abort(404, description="Project not found")
        _write_all(keep)

    path = os.path.join(UPLOAD_DIR, removed["stored_filename"])
    if os.path.exists(path):
        os.remove(path)
    return jsonify({"deleted": pid})


# --------------------------------------------------------------------------
# Error handling -> always return JSON
# --------------------------------------------------------------------------
@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(413)
def json_error(err):
    code = getattr(err, "code", 500)
    msg = getattr(err, "description", str(err))
    if code == 413:
        msg = f"File too large. Limit is {MAX_CONTENT_MB} MB."
    return jsonify({"error": msg, "status": code}), code


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)
