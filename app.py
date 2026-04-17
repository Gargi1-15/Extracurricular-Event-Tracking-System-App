from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)


def _database_uri():
    uri = os.environ.get("DATABASE_URL", "").strip()
    if not uri:
        return "sqlite:///events.db"
    if uri.startswith("postgres://"):
        return uri.replace("postgres://", "postgresql://", 1)
    return uri


app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = _database_uri()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    registrations = db.relationship("Registration", back_populates="student", cascade="all, delete-orphan")


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80), nullable=True)
    location = db.Column(db.String(120), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    capacity = db.Column(db.Integer, nullable=True)

    registrations = db.relationship("Registration", back_populates="event", cascade="all, delete-orphan")


class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="registrations")
    event = db.relationship("Event", back_populates="registrations")


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def init_db():
    with app.app_context():
        db.create_all()
        seed_sample_data()


def seed_sample_data():
    if Event.query.count() > 0:
        return

    sample_events = [
        Event(
            title="Tech Talk: AI in Education",
            description="A beginner-friendly session exploring how AI is transforming learning.",
            category="Technology",
            location="Auditorium A",
            date=datetime(2026, 4, 20).date(),
            start_time=datetime.strptime("15:00", "%H:%M").time(),
            end_time=datetime.strptime("17:00", "%H:%M").time(),
            capacity=80,
        ),
        Event(
            title="Intercollege Football Tournament",
            description="Join the annual football tournament. Open for all skill levels.",
            category="Sports",
            location="Main Ground",
            date=datetime(2026, 4, 25).date(),
            start_time=datetime.strptime("09:00", "%H:%M").time(),
            end_time=datetime.strptime("17:00", "%H:%M").time(),
            capacity=22,
        ),
        Event(
            title="Photography Workshop",
            description="Hands-on workshop on smartphone and DSLR photography.",
            category="Arts",
            location="Studio 3",
            date=datetime(2026, 5, 2).date(),
            start_time=datetime.strptime("11:00", "%H:%M").time(),
            end_time=datetime.strptime("14:00", "%H:%M").time(),
            capacity=40,
        ),
    ]

    db.session.add_all(sample_events)
    db.session.commit()


@app.route("/")
def home():
    events = Event.query.order_by(Event.date, Event.start_time).all()
    summary = {
        "total_events": Event.query.count(),
        "total_registrations": Registration.query.count(),
        "unique_students": Student.query.count(),
    }
    return render_template("index.html", events=events, summary=summary)


@app.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    subject = request.form.get("subject", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not subject or not message:
        flash("Please fill in all contact fields.", "warning")
        return redirect(url_for("home") + "#contact")

    contact_message = ContactMessage(
        name=name,
        email=email,
        subject=subject,
        message=message,
    )
    db.session.add(contact_message)
    db.session.commit()

    flash("Thanks for contacting us. We will get back to you soon.", "success")
    return redirect(url_for("home") + "#contact")


@app.route("/events/<int:event_id>")
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template("event_detail.html", event=event)


@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    event_id = request.form.get("event_id")

    if not name or not email or not event_id:
        flash("Please fill in all fields.", "danger")
        return redirect(request.referrer or url_for("home"))

    event = Event.query.get_or_404(event_id)

    student = Student.query.filter_by(email=email).first()
    if not student:
        student = Student(name=name, email=email)
        db.session.add(student)
        db.session.flush()

    existing = Registration.query.filter_by(student_id=student.id, event_id=event.id).first()
    if existing:
        flash("You are already registered for this event.", "info")
        return redirect(url_for("event_detail", event_id=event.id))

    if event.capacity is not None and len(event.registrations) >= event.capacity:
        flash("This event is full.", "warning")
        return redirect(url_for("event_detail", event_id=event.id))

    registration = Registration(student=student, event=event)
    db.session.add(registration)
    db.session.commit()

    flash("Successfully registered!", "success")
    return redirect(url_for("event_detail", event_id=event.id))


@app.route("/admin")
def admin_login():
    return render_template("admin_login.html")


@app.route("/admin/auth", methods=["POST"])
def admin_auth():
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "").strip()

    if username == "admin" and password == "password":
        resp = redirect(url_for("admin_events"))
        resp.set_cookie("admin", "1", max_age=3600)
        return resp

    flash("Invalid credentials", "danger")
    return redirect(url_for("admin_login"))


def require_admin():
    if request.cookies.get("admin") != "1":
        return False
    return True


@app.route("/admin/events")
def admin_events():
    if not require_admin():
        return redirect(url_for("admin_login"))

    events = Event.query.order_by(Event.date, Event.start_time).all()
    return render_template("admin_events.html", events=events)


@app.route("/admin/events/create", methods=["GET", "POST"])
def admin_create_event():
    if not require_admin():
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip() or None
        location = request.form.get("location", "").strip()
        date_str = request.form.get("date")
        start_time_str = request.form.get("start_time")
        end_time_str = request.form.get("end_time")
        capacity_str = request.form.get("capacity")

        if not title or not description or not location or not date_str or not start_time_str or not end_time_str:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("admin_create_event"))

        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()
        except ValueError:
            flash("Invalid date or time format.", "danger")
            return redirect(url_for("admin_create_event"))

        capacity = int(capacity_str) if capacity_str else None

        event = Event(
            title=title,
            description=description,
            category=category,
            location=location,
            date=date,
            start_time=start_time,
            end_time=end_time,
            capacity=capacity,
        )
        db.session.add(event)
        db.session.commit()

        flash("Event created.", "success")
        return redirect(url_for("admin_events"))

    return render_template("admin_event_form.html", event=None)


@app.route("/admin/events/<int:event_id>/edit", methods=["GET", "POST"])
def admin_edit_event(event_id):
    if not require_admin():
        return redirect(url_for("admin_login"))

    event = Event.query.get_or_404(event_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip() or None
        location = request.form.get("location", "").strip()
        date_str = request.form.get("date")
        start_time_str = request.form.get("start_time")
        end_time_str = request.form.get("end_time")
        capacity_str = request.form.get("capacity")

        if not title or not description or not location or not date_str or not start_time_str or not end_time_str:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("admin_edit_event", event_id=event.id))

        try:
            event.date = datetime.strptime(date_str, "%Y-%m-%d").date()
            event.start_time = datetime.strptime(start_time_str, "%H:%M").time()
            event.end_time = datetime.strptime(end_time_str, "%H:%M").time()
        except ValueError:
            flash("Invalid date or time format.", "danger")
            return redirect(url_for("admin_edit_event", event_id=event.id))

        event.title = title
        event.description = description
        event.category = category
        event.location = location
        event.capacity = int(capacity_str) if capacity_str else None

        db.session.commit()
        flash("Event updated.", "success")
        return redirect(url_for("admin_events"))

    return render_template("admin_event_form.html", event=event)


@app.route("/admin/events/<int:event_id>/delete", methods=["POST"])
def admin_delete_event(event_id):
    if not require_admin():
        return redirect(url_for("admin_login"))

    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted.", "info")
    return redirect(url_for("admin_events"))


@app.route("/dashboard")
def dashboard():
    events = Event.query.order_by(Event.date).all()
    students = Student.query.order_by(Student.created_at.desc()).all()

    event_participation = [
        {"label": e.title, "count": len(e.registrations)} for e in events
    ]

    student_participation = [
        {"label": s.name, "count": len(s.registrations)} for s in students
    ]

    total_registrations = Registration.query.count()
    unique_students = Student.query.count()
    total_events = Event.query.count()

    summary = {
        "total_registrations": total_registrations,
        "unique_students": unique_students,
        "total_events": total_events,
    }

    return render_template(
        "dashboard.html",
        event_participation=event_participation,
        student_participation=student_participation,
        summary=summary,
    )


@app.route("/api/recommendations")
def recommendations_api():
    email = request.args.get("email", "").strip().lower()

    student = Student.query.filter_by(email=email).first()
    if not student:
        upcoming = (
            Event.query.filter(Event.date >= datetime.utcnow().date())
            .order_by(Event.date, Event.start_time)
            .limit(3)
            .all()
        )
        return jsonify(
            {
                "strategy": "cold_start",
                "events": [
                    {"id": e.id, "title": e.title, "category": e.category, "date": e.date.isoformat()}
                    for e in upcoming
                ],
            }
        )

    categories = {}
    for reg in student.registrations:
        cat = reg.event.category or "General"
        categories[cat] = categories.get(cat, 0) + 1

    favorite_category = None
    if categories:
        favorite_category = max(categories, key=categories.get)

    query = Event.query.filter(Event.date >= datetime.utcnow().date())
    if favorite_category:
        query = query.filter(Event.category == favorite_category)

    recommended = query.order_by(Event.date, Event.start_time).limit(5).all()

    return jsonify(
        {
            "strategy": "simple_preferences",
            "favorite_category": favorite_category,
            "events": [
                {"id": e.id, "title": e.title, "category": e.category, "date": e.date.isoformat()}
                for e in recommended
            ],
        }
    )


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", host="0.0.0.0", port=port)


# Needed for production WSGI servers (gunicorn/uwsgi) where __main__ is not executed.
if __name__ != "__main__":
    init_db()

