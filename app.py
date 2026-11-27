from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime, date, timedelta

app = Flask(__name__)


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection


# ==========================================
# CREATE AND UPDATE DATABASE TABLE
# ==========================================

def create_table():

    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT DEFAULT 'Upcoming'
        )
    """)

    # Add new columns to existing databases
    columns = [
        ("last_reminded", "TEXT"),
        ("attempts", "INTEGER DEFAULT 0"),
        ("snoozed_until", "TEXT"),
        ("action_date", "TEXT"),
        ("caregiver_alerted", "INTEGER DEFAULT 0")
    ]

    existing = [
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(medicines)"
        ).fetchall()
    ]

    for column, datatype in columns:
        if column not in existing:
            connection.execute(
                f"ALTER TABLE medicines ADD COLUMN {column} {datatype}"
            )

    connection.commit()
    connection.close()


# ==========================================
# RESET STATUS FOR A NEW DAY
# ==========================================

def reset_daily_status():

    today = date.today().isoformat()

    connection = get_db_connection()

    connection.execute("""
        UPDATE medicines
        SET status = 'Upcoming',
            attempts = 0,
            last_reminded = NULL,
            snoozed_until = NULL,
            action_date = ?,
            caregiver_alerted = 0
        WHERE action_date IS NULL OR action_date != ?
    """, (today, today))

    connection.commit()
    connection.close()


# ==========================================
# HTML PAGE ROUTES
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/medicines")
def medicines_page():
    return render_template("medicines.html")


@app.route("/reminders")
def reminders_page():
    return render_template("reminders.html")


# ==========================================
# ADD MEDICINE
# ==========================================

@app.route("/add_medicine", methods=["POST"])
def add_medicine():

    data = request.get_json() or {}

    name = data.get("name")
    dosage = data.get("dosage")
    time = data.get("time")

    if not name or not dosage or not time:
        return jsonify({"error": "All fields are required"}), 400

    try:
        datetime.strptime(time, "%H:%M")
    except ValueError:
        return jsonify({"error": "Invalid time format"}), 400

    connection = get_db_connection()

    connection.execute("""
        INSERT INTO medicines (name, dosage, time, action_date)
        VALUES (?, ?, ?, ?)
    """, (name, dosage, time, date.today().isoformat()))

    connection.commit()
    connection.close()

    return jsonify({"message": "Medicine added successfully"})


# ==========================================
# GET ALL MEDICINES
# ==========================================

@app.route("/get_medicines", methods=["GET"])
def get_medicines():

    reset_daily_status()

    connection = get_db_connection()

    medicines = connection.execute(
        "SELECT * FROM medicines ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return jsonify([dict(medicine) for medicine in medicines])


# ==========================================
# RECORD NOTIFICATION ATTEMPT
# ==========================================

@app.route("/record_attempt/<int:medicine_id>", methods=["POST"])
def record_attempt(medicine_id):

    connection = get_db_connection()

    medicine = connection.execute(
        "SELECT * FROM medicines WHERE id = ?",
        (medicine_id,)
    ).fetchone()

    if medicine is None:
        connection.close()
        return jsonify({"error": "Medicine not found"}), 404

    if medicine["status"] in ("Taken", "Missed"):
        connection.close()
        return jsonify({"error": "Reminder is already completed"}), 400

    attempts = medicine["attempts"] + 1

    caregiver_alerted = 1 if attempts >= 3 else 0

    connection.execute("""
        UPDATE medicines
        SET attempts = ?,
            last_reminded = ?,
            caregiver_alerted = ?
        WHERE id = ?
    """, (
        attempts,
        datetime.now().isoformat(timespec="seconds"),
        caregiver_alerted,
        medicine_id
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "attempts": attempts,
        "caregiver_alert_due": bool(caregiver_alerted)
    })


# ==========================================
# SNOOZE REMINDER
# ==========================================

@app.route("/snooze_reminder/<int:medicine_id>", methods=["POST"])
def snooze_reminder(medicine_id):

    snooze_time = (
        datetime.now() + timedelta(minutes=10)
    ).isoformat(timespec="seconds")

    connection = get_db_connection()

    cursor = connection.execute("""
        UPDATE medicines
        SET status = 'Snoozed',
            snoozed_until = ?
        WHERE id = ?
    """, (snooze_time, medicine_id))

    connection.commit()
    connection.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Medicine not found"}), 404

    return jsonify({"message": "Reminder snoozed for 10 minutes"})


# ==========================================
# DELETE MEDICINE
# ==========================================

@app.route("/delete_medicine/<int:medicine_id>", methods=["DELETE"])
def delete_medicine(medicine_id):

    connection = get_db_connection()

    connection.execute(
        "DELETE FROM medicines WHERE id = ?",
        (medicine_id,)
    )

    connection.commit()
    connection.close()

    return jsonify({"message": "Medicine deleted successfully"})


# ==========================================
# UPDATE MEDICINE STATUS
# ==========================================

@app.route("/update_status/<int:medicine_id>", methods=["PUT"])
def update_status(medicine_id):

    data = request.get_json() or {}
    status = data.get("status")

    allowed_statuses = [
        "Upcoming", "Taken", "Missed", "Snoozed"
    ]

    if status not in allowed_statuses:
        return jsonify({"error": "Invalid status"}), 400

    connection = get_db_connection()

    cursor = connection.execute("""
        UPDATE medicines
        SET status = ?,
            action_date = ?,
            snoozed_until = NULL
        WHERE id = ?
    """, (status, date.today().isoformat(), medicine_id))

    connection.commit()
    connection.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Medicine not found"}), 404

    return jsonify({"message": "Status updated successfully"})


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    create_table()

    app.run(debug=True)