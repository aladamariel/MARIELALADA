
import sqlite3
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

CLASSMATE_API_URL = "https://abordaje-jm.onrender.com/students"


# Connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect("students.db")
    conn.row_factory = sqlite3.Row
    return conn


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Existing Student Information API
@app.route("/student")
def get_student():
    return jsonify({
        "student_id": "24-00357",
        "name": "Mariel Alada",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


# Existing Say Hello API
@app.route("/hello")
def say_hello():
    name = request.args.get("name", "Student")
    return jsonify({"message": f"Hello, {name}!"})


# Existing Attendance API
@app.route("/attendance")
def get_attendance():
    return jsonify({
        "student_name": "Mariel Alada",
        "attendance_status": "Present",
        "attendance_percentage": 95
    })


# READ: Get all students from your database
@app.route("/students")
def get_students():
    conn = get_db_connection()
    try:
        students = conn.execute(
            "SELECT * FROM students"
        ).fetchall()
        return jsonify([dict(student) for student in students])
    finally:
        conn.close()


# READ: Get all students for your CRUD API
@app.route("/api/students", methods=["GET"])
def api_get_students():
    conn = get_db_connection()
    try:
        students = conn.execute(
            "SELECT * FROM students"
        ).fetchall()
        return jsonify([dict(student) for student in students])
    finally:
        conn.close()


# CREATE: Add a new student
@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Please provide student data in JSON format"
        }), 400

    required_fields = [
        "student_id", "name", "program", "year", "section"
    ]

    missing = [
        field for field in required_fields
        if field not in data or data[field] is None or data[field] == ""
    ]

    if missing:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing
        }), 400

    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO students
            (student_id, name, program, year, section)
            VALUES (?, ?, ?, ?, ?)""",
            (
                data["student_id"],
                data["name"],
                data["program"],
                data["year"],
                data["section"]
            )
        )
        conn.commit()

        return jsonify({
            "message": "Student added successfully",
            "id": cursor.lastrowid
        }), 201

    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({
            "error": "Could not add student. Check for duplicate IDs or invalid data."
        }), 400
    finally:
        conn.close()


# READ: Get one student by database ID
@app.route("/students/<int:id>")
def get_student_by_id(id):
    conn = get_db_connection()
    try:
        student = conn.execute(
            "SELECT * FROM students WHERE id = ?", (id,)
        ).fetchone()

        if student is None:
            return jsonify({"error": "Student not found"}), 404

        return jsonify(dict(student))
    finally:
        conn.close()


# UPDATE: Edit a student by database ID
@app.route("/api/students/<int:id>", methods=["PUT"])
def update_student(id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Please provide updated student data in JSON format"
        }), 400

    required_fields = [
        "student_id", "name", "program", "year", "section"
    ]

    missing = [
        field for field in required_fields
        if field not in data or data[field] is None or data[field] == ""
    ]

    if missing:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing
        }), 400

    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """UPDATE students
            SET student_id = ?, name = ?, program = ?,
                year = ?, section = ?
            WHERE id = ?""",
            (
                data["student_id"],
                data["name"],
                data["program"],
                data["year"],
                data["section"],
                id
            )
        )
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Student not found"}), 404

        return jsonify({"message": "Student updated successfully"})

    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({
            "error": "Could not update student. Check for duplicate IDs or invalid data."
        }), 400
    finally:
        conn.close()


# DELETE: Remove a student from your database
@app.route("/api/students/<int:id>", methods=["DELETE"])
def delete_student(id):
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM students WHERE id = ?", (id,)
        )
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Student not found"}), 404

        return jsonify({"message": "Student deleted successfully"})
    finally:
        conn.close()


# Additional task: Get students by section
@app.route("/students/section/<section>")
def get_students_by_section(section):
    conn = get_db_connection()
    try:
        students = conn.execute(
            "SELECT * FROM students WHERE section = ?", (section,)
        ).fetchall()
        return jsonify([dict(student) for student in students])
    finally:
        conn.close()


# CLASSMATE API: Fetch records through your Flask server
@app.route("/api/classmate-students", methods=["GET"])
def get_classmate_students():
    # Only allow the expected HTTPS endpoint.
    supplied_url = request.args.get("url", CLASSMATE_API_URL)
    parsed = urlparse(supplied_url)

    if (
        parsed.scheme != "https"
        or parsed.hostname != "abordaje-jm.onrender.com"
        or parsed.path.rstrip("/") != "/students"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
    ):
        return jsonify({
            "error": "Use the classmate API URL ending in /students."
        }), 400

    api_request = Request(
        CLASSMATE_API_URL,
        headers={"Accept": "application/json", "User-Agent": "StudentManagementSystem/1.0"}
    )

    try:
        with urlopen(api_request, timeout=20) as response:
            if response.status != 200:
                return jsonify({
                    "error": f"Classmate API returned HTTP {response.status}."
                }), 502

            data = json.loads(response.read().decode("utf-8"))

        # Accept a JSON list or common object-wrapped list formats.
        if isinstance(data, dict):
            for key in ("students", "data", "records", "results"):
                if isinstance(data.get(key), list):
                    data = data[key]
                    break

        if not isinstance(data, list):
            return jsonify({
                "error": "The classmate API did not return a JSON list of students."
            }), 502

        return jsonify(data)

    except HTTPError as error:
        return jsonify({
            "error": f"Classmate API returned HTTP {error.code}."
        }), 502
    except URLError:
        app.logger.exception("Could not connect to classmate API")
        return jsonify({
            "error": "Could not connect to the classmate API. Try again later."
        }), 502
    except (TimeoutError, OSError):
        app.logger.exception("Classmate API connection failed")
        return jsonify({
            "error": "The classmate API timed out or could not be reached."
        }), 502
    except (json.JSONDecodeError, UnicodeDecodeError):
        return jsonify({
            "error": "The classmate API did not return valid JSON."
        }), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
