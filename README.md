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

## 2.1 Deploy notes (important)

For cloud deploy (Render/Railway/Fly/etc):

- Use start command:
  - `gunicorn app:app`
- Set environment variables:
  - `SECRET_KEY=<your-random-secret>`
  - `DATABASE_URL=<your-db-url>` (optional; defaults to local SQLite)
- If provider gives Postgres URL as `postgres://...`, the app auto-converts it to `postgresql://...`.

If you deploy with SQLite, ensure the platform supports persistent disk storage.  
Otherwise data may reset on restart.

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

