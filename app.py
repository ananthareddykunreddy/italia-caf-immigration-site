import json
import os
import sqlite3
import uuid
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
DATABASE_PATH = DATA_DIR / "site.db"
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "doc", "docx"}


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "change-this-secret")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)


CAF_SERVICES = {
    "isee": {
        "name": "ISEE",
        "summary": "Support for ISEE document preparation and appointment-ready file organization.",
        "items": [
            "Household and family document review",
            "Income and supporting file preparation",
            "Appointment file organization",
            "General ISEE assistance",
        ],
    },
    "730": {
        "name": "730",
        "summary": "Assistance for 730 declaration paperwork and related supporting documents.",
        "items": [
            "730 document preparation",
            "Income and deduction file review",
            "Household tax document organization",
            "General declaration support",
        ],
    },
    "imu": {
        "name": "IMU",
        "summary": "Support for IMU-related paperwork and payment preparation.",
        "items": [
            "IMU document checks",
            "Property-related paperwork organization",
            "Payment document preparation",
            "General IMU support",
        ],
    },
    "red-icric": {
        "name": "RED / ICRIC",
        "summary": "Support for RED and ICRIC documentation and case preparation.",
        "items": [
            "RED file preparation",
            "ICRIC supporting document checks",
            "Submission-ready file organization",
            "General assistance for recurring updates",
        ],
    },
    "cambio-residenza": {
        "name": "Cambio Residenza",
        "summary": "Support for change of residence paperwork and related municipal document preparation.",
        "items": [
            "Residence change document support",
            "Municipal paperwork organization",
            "Supporting file checks",
            "Appointment preparation assistance",
        ],
    },
    "f24": {
        "name": "F24",
        "summary": "Assistance for F24 preparation and payment-related document organization.",
        "items": [
            "F24 form support",
            "Payment document checks",
            "Tax and contribution file organization",
            "General F24-related assistance",
        ],
    },
    "bonus": {
        "name": "Bonus",
        "summary": "Support for bonus-related documentation and eligibility file preparation.",
        "items": [
            "Bonus-related document intake",
            "Eligibility file organization",
            "Supporting copy preparation",
            "Submission-ready documentation support",
        ],
    },
    "spid": {
        "name": "SPID",
        "summary": "Assistance for SPID activation readiness and supporting identity document checks.",
        "items": [
            "Identity document preparation",
            "Contact and account setup readiness",
            "Supporting file review",
            "General SPID assistance",
        ],
    },
}


def ensure_directories() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db() -> None:
    db = sqlite3.connect(DATABASE_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            service_type TEXT NOT NULL,
            preferred_date TEXT NOT NULL,
            preferred_time TEXT NOT NULL,
            city TEXT NOT NULL,
            notes TEXT,
            uploaded_files TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()
    db.close()


@app.teardown_appcontext
def close_db(_exception) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def store_uploaded_files(files) -> list[dict]:
    stored_files = []
    for incoming_file in files:
        if not incoming_file or not incoming_file.filename:
            continue

        if not allowed_file(incoming_file.filename):
            continue

        original_name = secure_filename(incoming_file.filename)
        unique_name = f"{uuid.uuid4().hex}_{original_name}"
        incoming_file.save(UPLOAD_DIR / unique_name)
        stored_files.append({"stored_name": unique_name, "original_name": original_name})

    return stored_files


def admin_logged_in() -> bool:
    return bool(session.get("admin_logged_in"))


def require_admin():
    if not admin_logged_in():
        flash("Please sign in to view records.", "error")
        return redirect(url_for("admin_login"))
    return None


@app.context_processor
def inject_globals():
    return {"business_name": "ANI Italia Hub"}


ensure_directories()
init_db()


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/services")
def services():
    return render_template("services.html")


@app.route("/caf-services")
def caf_services():
    return render_template("caf_services.html", caf_services=CAF_SERVICES)


@app.route("/caf-services/<slug>")
def caf_service_detail(slug: str):
    service = CAF_SERVICES.get(slug)
    if not service:
        return redirect(url_for("caf_services"))
    return render_template("caf_service_detail.html", service=service, slug=slug)


@app.route("/embassy-services")
def embassy_services():
    return render_template("embassy_services.html")


@app.route("/immigration-services")
def immigration_services():
    return render_template("immigration_services.html")


@app.route("/appointments", methods=["GET", "POST"])
def appointments():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        service_type = request.form.get("service_type", "").strip()
        preferred_date = request.form.get("preferred_date", "").strip()
        preferred_time = request.form.get("preferred_time", "").strip()
        city = request.form.get("city", "").strip()
        notes = request.form.get("notes", "").strip()

        if not all([full_name, email, phone, service_type, preferred_date, preferred_time, city]):
            flash("Please complete all required appointment fields.", "error")
            return redirect(url_for("appointments"))

        uploaded_files = store_uploaded_files(request.files.getlist("documents"))
        db = get_db()
        db.execute(
            """
            INSERT INTO appointments (
                full_name, email, phone, service_type, preferred_date,
                preferred_time, city, notes, uploaded_files
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                full_name,
                email,
                phone,
                service_type,
                preferred_date,
                preferred_time,
                city,
                notes,
                json.dumps(uploaded_files),
            ),
        )
        db.commit()
        flash("Appointment request saved successfully.", "success")
        return redirect(url_for("appointments"))

    return render_template("appointments.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        supplied_password = request.form.get("password", "")
        expected_password = os.environ.get("ADMIN_PASSWORD", "change-me-now")
        if supplied_password == expected_password:
            session["admin_logged_in"] = True
            flash("Signed in successfully.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Incorrect password.", "error")
        return redirect(url_for("admin_login"))

    return render_template("admin_login.html")


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    flash("Signed out.", "success")
    return redirect(url_for("home"))


@app.route("/admin/dashboard")
def admin_dashboard():
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response

    rows = get_db().execute(
        """
        SELECT id, full_name, email, phone, service_type, preferred_date,
               preferred_time, city, notes, uploaded_files, created_at
        FROM appointments
        ORDER BY datetime(created_at) DESC, id DESC
        """
    ).fetchall()

    appointments_data = []
    for row in rows:
        item = dict(row)
        item["uploaded_files"] = json.loads(item["uploaded_files"] or "[]")
        appointments_data.append(item)

    return render_template("admin_dashboard.html", appointments=appointments_data)


@app.route("/admin/uploads/<path:filename>")
def admin_upload(filename: str):
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response

    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8001")),
        debug=False,
    )
