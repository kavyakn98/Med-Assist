
from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection


# ==========================================
# CREATE DATABASE TABLE
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

    data = request.get_json()

    name = data.get("name")
    dosage = data.get("dosage")
    time = data.get("time")

    if not name or not dosage or not time:
        return jsonify({"error": "All fields are required"}), 400

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO medicines (name, dosage, time)
        VALUES (?, ?, ?)
        """,
        (name, dosage, time)
    )

    connection.commit()
    connection.close()

    return jsonify({"message": "Medicine added successfully"})


# ==========================================
# GET ALL MEDICINES
# ==========================================

@app.route("/get_medicines", methods=["GET"])
def get_medicines():

    connection = get_db_connection()

    medicines = connection.execute(
        "SELECT * FROM medicines ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return jsonify([dict(medicine) for medicine in medicines])


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

    data = request.get_json()
    status = data.get("status")

    allowed_statuses = [
        "Upcoming",
        "Taken",
        "Missed",
        "Snoozed"
    ]

    if status not in allowed_statuses:
        return jsonify({"error": "Invalid status"}), 400

    connection = get_db_connection()

    connection.execute(
        "UPDATE medicines SET status = ? WHERE id = ?",
        (status, medicine_id)
    )

    connection.commit()
    connection.close()

    return jsonify({"message": "Status updated successfully"})


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    create_table()

    app.run(debug=True)
