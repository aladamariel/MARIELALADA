
from flask import Flask, jsonify, request, render_template
import sqlite3
import requests

app = Flask(__name__)

DATABASE = "students.db"

# Classmate's deployed API
CLASSMATE_API_URL = "https://agagdangerich.onrender.com/api/students"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def student_to_dict(student):
    return {
        "student_id": student["student_id"],
        "name": student["name"],
        "program": student["program"],
        "year": student["year"],
        "section": student["section"],
        "source": student["source"]
    }


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# GET STUDENT INFORMATION
# ==========================================

@app.route("/student", methods=["GET"])
def get_student():

    return jsonify({
        "student_id": "24-00357",
        "name": "Mariel Alada",
        "program": "BSIT",
        "year": 3,
        "section": "A",
        "source": "Local"
    })


# ==========================================
# GREETING API
# ==========================================

@app.route("/hello", methods=["GET"])
def hello():

    name = request.args.get("name", "Student")

    return jsonify({
        "message": f"Hello, {name}!"
    })


# ==========================================
# ATTENDANCE API
# ==========================================

@app.route("/attendance", methods=["GET"])
def attendance():

    return jsonify({
        "student_id": "24-00357",
        "name": "Mariel Alada",
        "status": "Present",
        "attendance_percentage": 95
    })


# ==========================================
# GET ALL LOCAL STUDENTS
# ==========================================

@app.route("/api/students", methods=["GET"])
def get_students():

    conn = get_db_connection()

    try:

        students = conn.execute(
            "SELECT * FROM students"
        ).fetchall()

        return jsonify([
            student_to_dict(student)
            for student in students
        ])

    except sqlite3.Error as error:

        return jsonify({
            "error": "Unable to retrieve students",
            "details": str(error)
        }), 500

    finally:
        conn.close()


# ==========================================
# ADD STUDENT
# ==========================================

@app.route("/api/students", methods=["POST"])
def add_student():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):

        return jsonify({
            "error": "Invalid or missing student data"
        }), 400

    required_fields = [
        "student_id",
        "name",
        "program",
        "year",
        "section"
    ]

    for field in required_fields:

        if field not in data or data[field] in [None, ""]:

            return jsonify({
                "error": f"Missing field: {field}"
            }), 400

    conn = get_db_connection()

    try:

        conn.execute("""
            INSERT INTO students
            (
                student_id,
                name,
                program,
                year,
                section,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data["student_id"],
            data["name"],
            data["program"],
            data["year"],
            data["section"],
            data.get("source", "Local")
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Student added successfully",
            "source": data.get("source", "Local")
        }), 201

    except sqlite3.IntegrityError:

        return jsonify({
            "error": "Student ID already exists"
        }), 409

    except sqlite3.Error as error:

        return jsonify({
            "error": "Database error",
            "details": str(error)
        }), 500

    finally:
        conn.close()


# ==========================================
# GET ONE STUDENT
# ==========================================

@app.route("/api/students/<student_id>", methods=["GET"])
def get_one_student(student_id):

    conn = get_db_connection()

    try:

        student = conn.execute(
            "SELECT * FROM students WHERE student_id = ?",
            (student_id,)
        ).fetchone()

        if student is None:

            return jsonify({
                "error": "Student not found"
            }), 404

        return jsonify(student_to_dict(student))

    except sqlite3.Error as error:

        return jsonify({
            "error": "Database error",
            "details": str(error)
        }), 500

    finally:
        conn.close()


# ==========================================
# UPDATE STUDENT
# ==========================================

@app.route("/api/students/<student_id>", methods=["PUT"])
def update_student(student_id):

    data = request.get_json(silent=True)

    if not isinstance(data, dict):

        return jsonify({
            "error": "Invalid update data"
        }), 400

    conn = get_db_connection()

    try:

        existing = conn.execute(
            "SELECT * FROM students WHERE student_id = ?",
            (student_id,)
        ).fetchone()

        if existing is None:

            return jsonify({
                "error": "Student not found"
            }), 404

        name = data.get("name", existing["name"])
        program = data.get("program", existing["program"])
        year = data.get("year", existing["year"])
        section = data.get("section", existing["section"])
        source = data.get("source", existing["source"])

        conn.execute("""
            UPDATE students
            SET name = ?,
                program = ?,
                year = ?,
                section = ?,
                source = ?
            WHERE student_id = ?
        """, (
            name,
            program,
            year,
            section,
            source,
            student_id
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Student updated successfully"
        }), 200

    except sqlite3.Error as error:

        return jsonify({
            "error": "Database error",
            "details": str(error)
        }), 500

    finally:
        conn.close()


# ==========================================
# DELETE STUDENT
# ==========================================

@app.route("/api/students/<student_id>", methods=["DELETE"])
def delete_student(student_id):

    conn = get_db_connection()

    try:

        student = conn.execute(
            "SELECT * FROM students WHERE student_id = ?",
            (student_id,)
        ).fetchone()

        if student is None:

            return jsonify({
                "error": "Student not found"
            }), 404

        conn.execute(
            "DELETE FROM students WHERE student_id = ?",
            (student_id,)
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Student deleted successfully"
        }), 200

    except sqlite3.Error as error:

        return jsonify({
            "error": "Database error",
            "details": str(error)
        }), 500

    finally:
        conn.close()


# ==========================================
# GET CLASSMATE RECORDS
# ==========================================

@app.route("/partner-records", methods=["GET"])
def get_partner_records():

    try:

        print("\n========== LOAD CLASSMATE RECORDS ==========")
        print("API URL:", CLASSMATE_API_URL)

        response = requests.get(
            CLASSMATE_API_URL,
            timeout=60
        )

        print("Status:", response.status_code)
        print("Response:", response.text)

        if not response.ok:

            return jsonify({
                "error": "Classmate API returned an HTTP error",
                "status_code": response.status_code,
                "details": response.text
            }), 502

        try:

            data = response.json()

        except ValueError:

            return jsonify({
                "error": "Classmate API returned invalid JSON",
                "details": response.text
            }), 502

        if isinstance(data, dict):

            data = data.get(
                "students",
                data.get("records", [])
            )

        if not isinstance(data, list):

            return jsonify({
                "error": "Expected a list of students",
                "response": data
            }), 502

        return jsonify(data), 200

    except requests.exceptions.Timeout:

        return jsonify({
            "error": "Classmate API timed out"
        }), 504

    except requests.exceptions.RequestException as error:

        print("GET API error:", str(error))

        return jsonify({
            "error": "Unable to connect to classmate API",
            "details": str(error)
        }), 502


# ==========================================
# IMPORT CLASSMATE STUDENT
# ==========================================

@app.route("/import-student", methods=["POST"])
def import_student():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):

        return jsonify({
            "error": "Invalid student data"
        }), 400

    required_fields = [
        "student_id",
        "name",
        "program",
        "year",
        "section"
    ]

    for field in required_fields:

        if field not in data or data[field] in [None, ""]:

            return jsonify({
                "error": f"Missing field: {field}"
            }), 400

    conn = get_db_connection()

    try:

        conn.execute("""
            INSERT INTO students
            (
                student_id,
                name,
                program,
                year,
                section,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data["student_id"],
            data["name"],
            data["program"],
            data["year"],
            data["section"],
            "Classmate API"
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Student imported successfully",
            "source": "Classmate API"
        }), 201

    except sqlite3.IntegrityError:

        return jsonify({
            "error": "Student already exists in local database"
        }), 409

    except sqlite3.Error as error:

        return jsonify({
            "error": "Database error",
            "details": str(error)
        }), 500

    finally:
        conn.close()


# ==========================================
# SEND STUDENT TO CLASSMATE API
# ==========================================

@app.route("/send-to-partner", methods=["POST"])
def send_to_partner():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):

        return jsonify({
            "success": False,
            "error": "Invalid student data"
        }), 400

    required_fields = [
        "student_id",
        "name",
        "program",
        "year",
        "section"
    ]

    for field in required_fields:

        if field not in data or data[field] in [None, ""]:

            return jsonify({
                "success": False,
                "error": f"Missing field: {field}"
            }), 400

    student_data = {
        "student_id": data["student_id"],
        "name": data["name"],
        "program": data["program"],
        "year": data["year"],
        "section": data["section"],
        "source": "External API"
    }

    try:

        print("\n========== SEND TO PARTNER ==========")
        print("URL:", CLASSMATE_API_URL)
        print("Data:", student_data)

        response = requests.post(
            CLASSMATE_API_URL,
            json=student_data,
            timeout=60
        )

        print("Partner status:", response.status_code)
        print("Partner response:", response.text)

        try:

            partner_response = response.json()

        except ValueError:

            partner_response = response.text

        # Successful HTTP response
        if response.status_code in [200, 201]:

            return jsonify({
                "success": True,
                "message": "Student successfully sent to classmate API",
                "student": student_data,
                "partner_response": partner_response
            }), 200

        # Partner rejected the request
        return jsonify({
            "success": False,
            "error": "Classmate API rejected the student",
            "status_code": response.status_code,
            "partner_response": partner_response
        }), 502

    except requests.exceptions.Timeout:

        print("Partner API timed out")

        return jsonify({
            "success": False,
            "error": "Classmate API timed out"
        }), 504

    except requests.exceptions.RequestException as error:

        print("Partner connection error:", str(error))

        return jsonify({
            "success": False,
            "error": "Unable to connect to classmate API",
            "details": str(error)
        }), 502


# ==========================================
# RUN FLASK APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
