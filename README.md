# Extracurricular Event Tracking System (Prototype)

A small Flask + SQLite web app for managing extracurricular events:

- **Students** can browse events, view details, and register.
- **Admins** can create, edit, and delete events.
- **System** tracks participation history.
- **Dashboard** visualizes student involvement.
- **Optional AI-style feature**: a simple recommendation endpoint that suggests events based on a student's past categories.

## 1. Setup

From `Mini Project` directory:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Run the app

```bash
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

The app will automatically create `events.db` (SQLite) and seed a few example events on first run.

## 3. Main screens

- **Student view** (home): list of upcoming events, recommendation box, links to event details.
- **Event detail**: full description and a registration form (name + email).
- **Admin**:
  - Login at `/admin` with `admin` / `password` (prototype only).
  - Manage events at `/admin/events` (create, edit, delete).
- **Dashboard** (`/dashboard`):
  - Cards with total registrations, unique students, and number of events.
  - Two charts: registrations per event, events per student.

## 4. Recommendation endpoint (prototype AI hook)

- Route: `/api/recommendations?email=you@example.edu`
- If the email has previous registrations, it recommends future events in their favorite category.
- If not, it falls back to a simple "cold start" list of upcoming events.

This endpoint is deliberately simple so you can later replace the logic with a real recommendation model.

## 5. Deploy (Render, Railway, or similar)

The repo includes **Gunicorn** and a **`Procfile`** so hosted platforms can run the app as a web process.

### Environment variables

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Long random string for sessions/cookies (required in production). |
| `DATABASE_URL` | Optional. If set (e.g. PostgreSQL from the host), the app uses it. If unset, SQLite `events.db` is used. |
| `PORT` | Usually set automatically by the host; Gunicorn binds to it. |
| `FLASK_ENV` | Set to `production` if you ever run `python app.py` on a server (disables debug). |

### Render (example)

1. Push this project to **GitHub**.
2. In Render: **New → Web Service**, connect the repo.
3. **Build command:** `pip install -r requirements.txt`
4. **Start command:** `gunicorn -w 2 -b 0.0.0.0:$PORT app:app` (or rely on `Procfile` if Render detects it).
5. Add **Environment** → `SECRET_KEY` = a random string (e.g. from a password generator).
6. Optional: add a **PostgreSQL** database and set `DATABASE_URL` to the connection string Render provides (the app already normalizes `postgres://` URLs).

**SQLite note:** On many hosts the filesystem is **ephemeral**—`events.db` can be wiped on redeploy. For a real deployment, use PostgreSQL (`DATABASE_URL`).

### Railway (example)

1. **New Project → Deploy from GitHub** (or CLI).
2. Railway sets `PORT` automatically.
3. Add variables: `SECRET_KEY`, and optionally provision **Postgres** and link it so `DATABASE_URL` is set.
4. Start command: `gunicorn -w 2 -b 0.0.0.0:$PORT app:app`

### Local test (production-style server)

```bash
set FLASK_ENV=production
gunicorn -w 2 -b 127.0.0.1:8000 app:app
```

Then open `http://127.0.0.1:8000`.
