# Extracurricular Event Tracking System (Prototype)

A small Flask + SQLite web app for managing extracurricular events:

- **Students** can browse events, view details, and register.
- **Admins** can create, edit, and delete events.
- **Admins** can mark events as paid and configure payment method/details.
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

## 5. Paid events and email notifications

- In admin event form, enable **"This is a paid event"** and add:
  - fee amount
  - payment method
  - payment details/instructions
- Students can see payment info on event detail page.
- If payment details are updated later, the app emails already-registered students.
- When a student registers for a paid event, the app also tries to send a confirmation mail with payment instructions.

### SMTP environment variables

Set these in your deployment platform (or local env) to enable email sending:

- `SMTP_HOST` (required for sending)
- `SMTP_PORT` (default: `587`)
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_FROM` (optional; defaults to `SMTP_USER`)
- `SMTP_USE_TLS` (`true` by default; set `false` only if your SMTP provider requires it)

