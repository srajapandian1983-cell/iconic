# SAM ICONIC Development Pvt Ltd — Real Estate

Website and project-upload backend for **SAM ICONIC Development Private Limited**.

- 195/28, Gandhi Road, West Tambaram, Chennai 600045
- Phone: 6385106308

**Live site:** https://srajapandian1983-cell.github.io/iconic/

## Contents

| Path | Description |
|------|-------------|
| [index.html](index.html) | Single-page real estate website (hero slideshow, services, featured properties, contact) |
| [backend/](backend/) | Flask API to upload project brochures as PDF with a description, backed by Supabase (Postgres table + Storage bucket) — see [backend/README.md](backend/README.md) |

## Run the website

Open `index.html` in any browser.

## Run the backend

Needs a Supabase project. See [backend/README.md](backend/README.md) for the
one-time schema setup and `.env` values.

```bash
cd backend
python -m pip install -r requirements.txt
copy .env.example .env          # then fill SUPABASE_SERVICE_ROLE_KEY
python app.py
```

API runs at `http://127.0.0.1:5000/`.
