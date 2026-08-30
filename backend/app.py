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
                "upload_page": "GET /upload  (browser form)",
                "list_projects": "GET /api/projects",
                "get_project": "GET /api/projects/<id>",
                "upload_project": "POST /api/projects  (multipart form: pdf, description, title?)",
                "download_pdf": "GET /api/projects/<id>/file",
                "delete_project": "DELETE /api/projects/<id>",
            },
        }
    )


UPLOAD_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Upload Project | SAM ICONIC Development</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Arial, Helvetica, sans-serif; background: #eef2f7; color: #333; }
  header { background: #1a3c5e; color: #fff; padding: 16px 20px; font-weight: bold; letter-spacing: 1px; }
  header span { color: #f0a500; }
  .wrap { max-width: 720px; margin: 24px auto; padding: 0 16px; }
  .card { background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 22px; margin-bottom: 22px; }
  h2 { color: #1a3c5e; font-size: 18px; margin-bottom: 16px; }
  label { display: block; font-size: 14px; font-weight: bold; color: #1a3c5e; margin: 12px 0 6px; }
  input[type=text], input[type=file], textarea {
    width: 100%; padding: 10px; border: 1px solid #ccd6e0; border-radius: 5px; font-size: 14px; font-family: inherit;
  }
  textarea { min-height: 80px; resize: vertical; }
  button { background: #f0a500; color: #1a3c5e; border: 0; padding: 11px 22px; border-radius: 5px;
    font-weight: bold; font-size: 14px; cursor: pointer; margin-top: 16px; }
  button:hover { background: #d99400; }
  button:disabled { opacity: .6; cursor: default; }
  #msg { margin-top: 14px; font-size: 14px; }
  .ok { color: #2f7d32; }
  .err { color: #c0392b; }
  .item { border-top: 1px solid #eee; padding: 12px 0; display: flex; justify-content: space-between; gap: 12px; }
  .item:first-of-type { border-top: 0; }
  .item .t { font-weight: bold; color: #1a3c5e; }
  .item .d { font-size: 13px; color: #666; }
  .item a { color: #1a3c5e; font-size: 13px; }
  .item .del { background: none; color: #c0392b; border: 1px solid #c0392b; padding: 4px 10px;
    font-size: 12px; border-radius: 4px; margin: 0; align-self: center; }
  .muted { color: #888; font-size: 14px; }
</style>
</head>
<body>
<header>SAM ICONIC <span>Development</span> Pvt Ltd &mdash; Project Upload</header>
<div class="wrap">

  <div class="card">
    <h2>Upload a project (PDF)</h2>
    <form id="f">
      <label for="pdf">PDF file *</label>
      <input type="file" id="pdf" name="pdf" accept="application/pdf,.pdf" required />
      <label for="title">Title</label>
      <input type="text" id="title" name="title" placeholder="e.g. Iconic Green Meadows" />
      <label for="description">Description *</label>
      <textarea id="description" name="description" placeholder="e.g. DTCP approved plots at West Tambaram, development in progress" required></textarea>
      <button type="submit" id="btn">Upload</button>
      <div id="msg"></div>
    </form>
  </div>

  <div class="card">
    <h2>Uploaded projects</h2>
    <div id="list" class="muted">Loading&hellip;</div>
  </div>

</div>
<script>
  var f = document.getElementById('f'), btn = document.getElementById('btn'), msg = document.getElementById('msg');

  function load() {
    fetch('/api/projects').then(function (r) { return r.json(); }).then(function (rows) {
      var el = document.getElementById('list');
      if (!rows.length) { el.className = 'muted'; el.textContent = 'No projects uploaded yet.'; return; }
      el.className = '';
      el.innerHTML = rows.map(function (p) {
        return '<div class="item"><div><div class="t">' + esc(p.title) + '</div>' +
          '<div class="d">' + esc(p.description) + '</div>' +
          '<a href="' + p.file_url + '" target="_blank" rel="noopener">View PDF &#8599;</a></div>' +
          '<button class="del" data-id="' + p.id + '">Delete</button></div>';
      }).join('');
    });
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  f.addEventListener('submit', function (e) {
    e.preventDefault();
    var file = document.getElementById('pdf').files[0];
    if (file) {
      var mb = file.size / 1048576;
      msg.className = 'muted';
      msg.textContent = 'Uploading ' + mb.toFixed(1) + ' MB…';
    }
    btn.disabled = true; btn.textContent = 'Uploading...';
    fetch('/api/projects', { method: 'POST', body: new FormData(f) })
      .then(function (r) {
        return r.text().then(function (t) {
          var j = null; try { j = JSON.parse(t); } catch (err) {}
          return { ok: r.ok, status: r.status, j: j, text: t };
        });
      })
      .then(function (res) {
        if (res.ok && res.j) {
          msg.className = 'ok'; msg.textContent = 'Uploaded: ' + res.j.title; f.reset(); load();
        } else {
          msg.className = 'err';
          msg.textContent = 'Error ' + res.status + ': ' +
            (res.j && res.j.error ? res.j.error : (res.text || 'upload failed').slice(0, 300));
        }
      })
      .catch(function (err) {
        msg.className = 'err';
        msg.textContent = 'Cannot reach the server. Is the black "Project Upload" ' +
          'window still open and showing "Running on http://127.0.0.1:5000"? ' +
          '(' + err + ')';
      })
      .finally(function () { btn.disabled = false; btn.textContent = 'Upload'; });
  });

  document.getElementById('list').addEventListener('click', function (e) {
    var b = e.target.closest('.del'); if (!b) return;
    if (!confirm('Delete this project?')) return;
    fetch('/api/projects/' + b.dataset.id, { method: 'DELETE' }).then(load);
  });

  load();
</script>
</body>
</html>"""


@app.get("/upload")
def upload_page():
    return UPLOAD_PAGE


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
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=True,
        threaded=True,
    )
