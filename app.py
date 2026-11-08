
import os
import sqlite3
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "students.db"
)

CLASSMATE_API_URL = "https://abordaje-jm.onrender.com/students"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                program TEXT NOT NULL,
                year INTEGER NOT NULL,
                section TEXT NOT NULL
            )
        """)


# ==========================================
# STUDENT VALIDATION
# ==========================================

def validate_student(data):
    required = [
        "student_id",
        "name",
        "program",
        "year",
        "section"
    ]

    missing = [
        field for field in required
        if data.get(field) is None
        or str(data.get(field)).strip() == ""
    ]

    if missing:
        return None, jsonify({
            "error": "Missing required fields",
            "fields": missing
        }), 400

    try:
        year = int(data["year"])

        if year < 1:
            raise ValueError

    except (TypeError, ValueError):
        return None, jsonify({
            "error": "Year must be a positive number"
        }), 400

    student = {
        "student_id": str(data["student_id"]).strip(),
        "name": str(data["name"]).strip(),
        "program": str(data["program"]).strip(),
        "year": year,
        "section": str(data["section"]).strip()
    }

    return student, None, None


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# STUDENT INFORMATION API
# ==========================================

@app.route("/student")
def student_info():
    return jsonify({
        "student_id": "2023-0001",
        "name": "Mariel Alada",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


# ==========================================
# GREETING API
# ==========================================

@app.route("/hello")
def hello():
    name = request.args.get("name", "Student")

    return jsonify({
        "message": f"Hello, {name}!"
    })


# ==========================================
# ATTENDANCE API
# ==========================================

@app.route("/attendance")
def attendance():
    return jsonify({
        "student_name": "Mariel Alada",
        "attendance_status": "Present",
        "attendance_percentage": 95
    })


# ==========================================
# GET ALL STUDENTS
# ==========================================

@app.route("/api/students", methods=["GET"])
def get_students():
    try:
        with get_db_connection() as connection:
            rows = connection.execute("""
                SELECT id, student_id, name, program, year, section
                FROM students
                ORDER BY id DESC
            """).fetchall()

        return jsonify([
            dict(row) for row in rows
        ])

    except sqlite3.Error:
        app.logger.exception("Failed to retrieve students")

        return jsonify({
            "error": "Database error while retrieving students."
        }), 500


# ==========================================
# ADD STUDENT
# ==========================================

@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.get_json(silent=True) or {}

    student, error, status = validate_student(data)

    if error:
        return error, status

    try:
        with get_db_connection() as connection:

            cursor = connection.execute("""
                INSERT INTO students
                (
                    student_id,
                    name,
                    program,
                    year,
                    section
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                student["student_id"],
                student["name"],
                student["program"],
                student["year"],
                student["section"]
            ))

            row = connection.execute("""
                SELECT id, student_id, name, program, year, section
                FROM students
                WHERE id = ?
            """, (
                cursor.lastrowid,
            )).fetchone()

        return jsonify(dict(row)), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "That Student ID already exists. Use a different ID."
        }), 409

    except sqlite3.Error:
        app.logger.exception("Failed to add student")

        return jsonify({
            "error": "Database error while adding student."
        }), 500


# ==========================================
# UPDATE STUDENT
# ==========================================

@app.route(
    "/api/students/<int:database_id>",
    methods=["PUT"]
)
def update_student(database_id):
    data = request.get_json(silent=True) or {}

    student, error, status = validate_student(data)

    if error:
        return error, status

    try:
        with get_db_connection() as connection:

            existing = connection.execute("""
                SELECT id
                FROM students
                WHERE id = ?
            """, (
                database_id,
            )).fetchone()

            if existing is None:
                return jsonify({
                    "error": "Student record not found."
                }), 404

            connection.execute("""
                UPDATE students
                SET
                    student_id = ?,
                    name = ?,
                    program = ?,
                    year = ?,
                    section = ?
                WHERE id = ?
            """, (
                student["student_id"],
                student["name"],
                student["program"],
                student["year"],
                student["section"],
                database_id
            ))

            row = connection.execute("""
                SELECT id, student_id, name, program, year, section
                FROM students
                WHERE id = ?
            """, (
                database_id,
            )).fetchone()

        return jsonify(dict(row))

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "That Student ID already exists. Use a different ID."
        }), 409

    except sqlite3.Error:
        app.logger.exception("Failed to update student")

        return jsonify({
            "error": "Database error while updating student."
        }), 500


# ==========================================
# DELETE STUDENT
# ==========================================

@app.route(
    "/api/students/<int:database_id>",
    methods=["DELETE"]
)
def delete_student(database_id):
    try:
        with get_db_connection() as connection:

            cursor = connection.execute("""
                DELETE FROM students
                WHERE id = ?
            """, (
                database_id,
            ))

            if cursor.rowcount == 0:
                return jsonify({
                    "error": "Student record not found."
                }), 404

        return jsonify({
            "message": "Student deleted successfully."
        })

    except sqlite3.Error:
        app.logger.exception("Failed to delete student")

        return jsonify({
            "error": "Database error while deleting student."
        }), 500


# ==========================================
# IMPORT CLASSMATE STUDENT
# ==========================================

@app.route("/import-student", methods=["POST"])
def import_student():
    data = request.get_json(silent=True) or {}

    student, error, status = validate_student(data)

    if error:
        return error, status

    try:
        with get_db_connection() as connection:

            # Check if the student already exists
            existing = connection.execute("""
                SELECT id
                FROM students
                WHERE student_id = ?
            """, (
                student["student_id"],
            )).fetchone()

            if existing:
                return jsonify({
                    "error": (
                        "This student already exists "
                        "in your database."
                    )
                }), 409

            # Insert the classmate's student record
            cursor = connection.execute("""
                INSERT INTO students
                (
                    student_id,
                    name,
                    program,
                    year,
                    section
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                student["student_id"],
                student["name"],
                student["program"],
                student["year"],
                student["section"]
            ))

            # Retrieve the newly saved record
            row = connection.execute("""
                SELECT id, student_id, name, program, year, section
                FROM students
                WHERE id = ?
            """, (
                cursor.lastrowid,
            )).fetchone()

        return jsonify({
            "message": "Classmate student saved successfully!",
            "student": dict(row)
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": (
                "This student already exists "
                "in your database."
            )
        }), 409

    except sqlite3.Error:
        app.logger.exception(
            "Failed to import classmate student"
        )

        return jsonify({
            "error": (
                "Database error while importing student."
            )
        }), 500


# ==========================================
# COMPATIBILITY ROUTES
# ==========================================

@app.route("/students")
def students_compat():
    return get_students()


@app.route("/students/<int:database_id>")
def student_compat_detail(database_id):
    try:
        with get_db_connection() as connection:

            row = connection.execute("""
                SELECT id, student_id, name, program, year, section
                FROM students
                WHERE id = ?
            """, (
                database_id,
            )).fetchone()

        if row is None:
            return jsonify({
                "error": "Student record not found."
            }), 404

        return jsonify(dict(row))

    except sqlite3.Error:
        app.logger.exception(
            "Failed to retrieve student details"
        )

        return jsonify({
            "error": "Database error."
        }), 500


@app.route("/students/section/<section>")
def students_by_section(section):
    try:
        with get_db_connection() as connection:

            rows = connection.execute("""
                SELECT id, student_id, name, program, year, section
                FROM students
                WHERE LOWER(section) = LOWER(?)
                ORDER BY name
            """, (
                section,
            )).fetchall()

        return jsonify([
            dict(row) for row in rows
        ])

    except sqlite3.Error:
        app.logger.exception(
            "Failed to retrieve students by section"
        )

        return jsonify({
            "error": "Database error."
        }), 500


# ==========================================
# CLASSMATE API INTEGRATION
# ==========================================

@app.route("/api/classmate-students", methods=["GET"])
def classmate_students():
    parsed = urlparse(CLASSMATE_API_URL)

    # Validate the classmate API URL
    if (
        parsed.scheme != "https"
        or parsed.hostname != "abordaje-jm.onrender.com"
    ):
        return jsonify({
            "error": "Classmate API URL is not allowed."
        }), 400

    try:
        req = Request(
            CLASSMATE_API_URL,
            headers={
                "Accept": "application/json"
            }
        )

        with urlopen(req, timeout=15) as response:
            result = response.read().decode("utf-8")

        return app.response_class(
            result,
            status=200,
            mimetype="application/json"
        )

    except HTTPError as error:
        app.logger.warning(
            "Classmate API returned HTTP error: %s",
            error.code
        )

        return jsonify({
            "error": (
                "Classmate API returned an error. "
                "Please try again later."
            )
        }), 502

    except (URLError, TimeoutError):
        app.logger.exception(
            "Could not connect to classmate API"
        )

        return jsonify({
            "error": (
                "Could not connect to the classmate API."
            )
        }), 502

    except Exception:
        app.logger.exception(
            "Unexpected error while retrieving classmate records"
        )

        return jsonify({
            "error": (
                "Unexpected error while retrieving classmate records."
            )
        }), 500


# ==========================================
# INITIALIZE DATABASE
# ==========================================

init_db()


# ==========================================
# RUN FLASK APPLICATION
# ==========================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
