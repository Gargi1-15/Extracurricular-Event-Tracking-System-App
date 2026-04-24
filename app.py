from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import smtplib
from email.message import EmailMessage
from sqlalchemy import text

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    if os.environ.get("VERCEL"):
        # Vercel serverless allows writes only in /tmp.
        database_url = "sqlite:////tmp/events.db"
    else:
        database_url = "sqlite:///events.db"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
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
    is_paid = db.Column(db.Boolean, nullable=False, default=False)
    fee_amount = db.Column(db.Float, nullable=True)
    payment_method = db.Column(db.String(120), nullable=True)
    payment_details = db.Column(db.Text, nullable=True)

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
        ensure_event_payment_columns()
        seed_sample_data()


def ensure_event_payment_columns():
    columns = {
        row[1]
        for row in db.session.execute(text("PRAGMA table_info(event)")).fetchall()
    }
    if "is_paid" not in columns:
        db.session.execute(
            text("ALTER TABLE event ADD COLUMN is_paid BOOLEAN NOT NULL DEFAULT 0")
        )
    if "fee_amount" not in columns:
        db.session.execute(text("ALTER TABLE event ADD COLUMN fee_amount FLOAT"))
    if "payment_method" not in columns:
        db.session.execute(text("ALTER TABLE event ADD COLUMN payment_method VARCHAR(120)"))
    if "payment_details" not in columns:
        db.session.execute(text("ALTER TABLE event ADD COLUMN payment_details TEXT"))
    db.session.commit()


def send_email(to_email, subject, body):
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user or "noreply@example.com")
    smtp_use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() != "false"

    if not smtp_host:
        return False, "SMTP is not configured"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            if smtp_use_tls:
                server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
        return True, "sent"
    except Exception as exc:
        return False, str(exc)


def notify_registered_students_payment_update(event):
    sent = 0
    failed = 0

    for reg in event.registrations:
        body = (
            f"Hello {reg.student.name},\n\n"
            f"Payment details were updated for the event '{event.title}'.\n"
            f"Date: {event.date.strftime('%d %b %Y')}\n"
            f"Time: {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}\n"
            f"Fee: {event.fee_amount if event.fee_amount is not None else 'N/A'}\n"
            f"Method: {event.payment_method or 'N/A'}\n"
            f"Details: {event.payment_details or 'N/A'}\n\n"
            "Please complete your payment as per the event instructions.\n"
        )
        ok, _ = send_email(
            reg.student.email,
            f"Payment update: {event.title}",
            body,
        )
        if ok:
            sent += 1
        else:
            failed += 1

    return sent, failed


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
    if event.is_paid:
        body = (
            f"Hello {student.name},\n\n"
            f"You are registered for '{event.title}'.\n"
            "This is a paid event. Please use the payment details below:\n\n"
            f"Fee: {event.fee_amount if event.fee_amount is not None else 'N/A'}\n"
            f"Method: {event.payment_method or 'N/A'}\n"
            f"Details: {event.payment_details or 'N/A'}\n"
        )
        ok, _ = send_email(student.email, f"Registration confirmed: {event.title}", body)
        if not ok:
            flash("Registration saved, but email notification is not configured.", "info")
    return redirect(url_for("event_detail", event_id=event.id))


@app.route("/my-registrations", methods=["GET", "POST"])
def my_registrations():
    email = request.values.get("email", "").strip().lower()
    student = None
    registrations = []

    if email:
        student = Student.query.filter_by(email=email).first()
        if student:
            registrations = (
                Registration.query.filter_by(student_id=student.id)
                .order_by(Registration.registered_at.desc())
                .all()
            )
        elif request.method == "POST":
            flash("No student found with this email.", "warning")

    return render_template(
        "my_registrations.html",
        email=email,
        student=student,
        registrations=registrations,
    )


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


@app.route("/admin/events/<int:event_id>/participants")
def admin_event_participants(event_id):
    if not require_admin():
        return redirect(url_for("admin_login"))

    event = Event.query.get_or_404(event_id)
    registrations = (
        Registration.query.filter_by(event_id=event.id)
        .order_by(Registration.registered_at.desc())
        .all()
    )
    return render_template(
        "admin_event_participants.html",
        event=event,
        registrations=registrations,
    )


@app.route("/admin/events/<int:event_id>/participants/<int:registration_id>/remove", methods=["POST"])
def admin_remove_participant(event_id, registration_id):
    if not require_admin():
        return redirect(url_for("admin_login"))

    event = Event.query.get_or_404(event_id)
    registration = Registration.query.get_or_404(registration_id)

    if registration.event_id != event.id:
        flash("Registration does not belong to this event.", "warning")
        return redirect(url_for("admin_event_participants", event_id=event.id))

    student_name = registration.student.name
    db.session.delete(registration)
    db.session.commit()
    flash(f"Removed {student_name} from {event.title}.", "success")
    return redirect(url_for("admin_event_participants", event_id=event.id))


@app.route("/admin/messages")
def admin_messages():
    if not require_admin():
        return redirect(url_for("admin_login"))

    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("admin_messages.html", messages=messages)


@app.route("/admin/messages/<int:message_id>/delete", methods=["POST"])
def admin_delete_message(message_id):
    if not require_admin():
        return redirect(url_for("admin_login"))

    contact_message = ContactMessage.query.get_or_404(message_id)
    db.session.delete(contact_message)
    db.session.commit()
    flash("Message deleted.", "info")
    return redirect(url_for("admin_messages"))


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
        is_paid = request.form.get("is_paid") == "on"
        fee_amount_str = request.form.get("fee_amount", "").strip()
        payment_method = request.form.get("payment_method", "").strip()
        payment_details = request.form.get("payment_details", "").strip()

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
        try:
            fee_amount = float(fee_amount_str) if fee_amount_str else None
        except ValueError:
            flash("Fee amount must be a valid number.", "warning")
            return redirect(url_for("admin_create_event"))
        if is_paid and (not payment_method or not payment_details):
            flash("For paid events, payment method and details are required.", "warning")
            return redirect(url_for("admin_create_event"))

        event = Event(
            title=title,
            description=description,
            category=category,
            location=location,
            date=date,
            start_time=start_time,
            end_time=end_time,
            capacity=capacity,
            is_paid=is_paid,
            fee_amount=fee_amount,
            payment_method=payment_method if is_paid else None,
            payment_details=payment_details if is_paid else None,
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
        is_paid = request.form.get("is_paid") == "on"
        fee_amount_str = request.form.get("fee_amount", "").strip()
        payment_method = request.form.get("payment_method", "").strip()
        payment_details = request.form.get("payment_details", "").strip()

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

        old_paid_state = (
            event.is_paid,
            event.fee_amount,
            event.payment_method,
            event.payment_details,
        )

        try:
            fee_amount = float(fee_amount_str) if fee_amount_str else None
        except ValueError:
            flash("Fee amount must be a valid number.", "warning")
            return redirect(url_for("admin_edit_event", event_id=event.id))
        if is_paid and (not payment_method or not payment_details):
            flash("For paid events, payment method and details are required.", "warning")
            return redirect(url_for("admin_edit_event", event_id=event.id))

        event.title = title
        event.description = description
        event.category = category
        event.location = location
        event.capacity = int(capacity_str) if capacity_str else None
        event.is_paid = is_paid
        event.fee_amount = fee_amount
        event.payment_method = payment_method if is_paid else None
        event.payment_details = payment_details if is_paid else None

        db.session.commit()
        new_paid_state = (
            event.is_paid,
            event.fee_amount,
            event.payment_method,
            event.payment_details,
        )
        if old_paid_state != new_paid_state and event.registrations:
            sent, failed = notify_registered_students_payment_update(event)
            if sent:
                flash(f"Payment update email sent to {sent} students.", "info")
            if failed:
                flash(f"Failed to send {failed} email(s). Check SMTP settings.", "warning")
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

    event_totals = []
    for event in events:
        registered_count = len(event.registrations)
        fill_rate = None
        if event.capacity:
            fill_rate = round((registered_count / event.capacity) * 100, 1)
        event_totals.append(
            {
                "id": event.id,
                "title": event.title,
                "category": event.category or "General",
                "date": event.date,
                "registered_count": registered_count,
                "capacity": event.capacity,
                "fill_rate": fill_rate,
            }
        )

    return render_template(
        "dashboard.html",
        event_participation=event_participation,
        student_participation=student_participation,
        summary=summary,
        event_totals=event_totals,
    )


@app.route("/api/recommendations")
def recommendations_api():
    email = request.args.get("email", "").strip().lower()
    today = datetime.utcnow().date()

    student = Student.query.filter_by(email=email).first()
    if not student:
        upcoming = (
            Event.query.filter(Event.date >= today)
            .order_by(Event.date, Event.start_time)
            .limit(3)
            .all()
        )
        # If there are no upcoming events, show the latest created events as fallback.
        if not upcoming:
            upcoming = Event.query.order_by(Event.date.desc(), Event.start_time.desc()).limit(3).all()
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

    query = Event.query.filter(Event.date >= today)
    if favorite_category:
        query = query.filter(Event.category == favorite_category)

    recommended = query.order_by(Event.date, Event.start_time).limit(5).all()
    if not recommended:
        # Relax category filter first.
        recommended = (
            Event.query.filter(Event.date >= today)
            .order_by(Event.date, Event.start_time)
            .limit(5)
            .all()
        )
    if not recommended:
        # As a final fallback, show latest events even if dates are in the past.
        recommended = Event.query.order_by(Event.date.desc(), Event.start_time.desc()).limit(5).all()

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


# Ensure tables exist in environments where __main__ is not executed
# (e.g., Vercel serverless importing the module).
init_db()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)

