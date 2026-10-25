
import sqlite3
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)


# Connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('students.db')
    conn.row_factory = sqlite3.Row
    return conn


# Home page
@app.route('/')
def home():
    return render_template('index.html')


# Existing Student Information API
@app.route('/student')
def get_student():
    return jsonify({
        "student_id": "24-00357",
        "name": "Mariel Alada",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })


# Existing Say Hello API
@app.route('/hello')
def say_hello():
    name = request.args.get('name', 'Student')
    return jsonify({
        "message": f"Hello, {name}!"
    })


# Existing Attendance API
@app.route('/attendance')
def get_attendance():
    return jsonify({
        "student_name": "Mariel Alada",
        "attendance_status": "Present",
        "attendance_percentage": 95
    })


# READ: Get all students from the database
@app.route('/students')
def get_students():
    conn = get_db_connection()

    students = conn.execute(
        'SELECT * FROM students'
    ).fetchall()

    conn.close()

    return jsonify([dict(student) for student in students])


# READ: Get all students for the CRUD API
@app.route('/api/students', methods=['GET'])
def api_get_students():
    conn = get_db_connection()

    students = conn.execute(
        'SELECT * FROM students'
    ).fetchall()

    conn.close()

    return jsonify([dict(student) for student in students])


# CREATE: Add a new student
@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Please provide student data in JSON format"
        }), 400

    required_fields = [
        'student_id', 'name', 'program', 'year', 'section'
    ]

    missing_fields = [
        field for field in required_fields
        if field not in data
    ]

    if missing_fields:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing_fields
        }), 400

    conn = get_db_connection()

    try:
        cursor = conn.execute(
            """INSERT INTO students
            (student_id, name, program, year, section)
            VALUES (?, ?, ?, ?, ?)""",
            (
                data['student_id'],
                data['name'],
                data['program'],
                data['year'],
                data['section']
            )
        )

        conn.commit()
        new_id = cursor.lastrowid

        return jsonify({
            "message": "Student added successfully",
            "id": new_id
        }), 201

    except sqlite3.IntegrityError:
        conn.rollback()

        return jsonify({
            "error": "Could not add student. Check for duplicate IDs or invalid data."
        }), 400

    finally:
        conn.close()


# READ: Get one student by database ID
@app.route('/students/<int:id>')
def get_student_by_id(id):
    conn = get_db_connection()

    student = conn.execute(
        'SELECT * FROM students WHERE id = ?',
        (id,)
    ).fetchone()

    conn.close()

    if student is None:
        return jsonify({"error": "Student not found"}), 404

    return jsonify(dict(student))


# UPDATE: Edit a student by database ID
@app.route('/api/students/<int:id>', methods=['PUT'])
def update_student(id):
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Please provide updated student data in JSON format"
        }), 400

    required_fields = [
        'student_id', 'name', 'program', 'year', 'section'
    ]

    missing_fields = [
        field for field in required_fields
        if field not in data
    ]

    if missing_fields:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing_fields
        }), 400

    conn = get_db_connection()

    try:
        cursor = conn.execute(
            """UPDATE students
            SET student_id = ?, name = ?, program = ?,
                year = ?, section = ?
            WHERE id = ?""",
            (
                data['student_id'],
                data['name'],
                data['program'],
                data['year'],
                data['section'],
                id
            )
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Student not found"
            }), 404

        return jsonify({
            "message": "Student updated successfully"
        })

    except sqlite3.IntegrityError:
        conn.rollback()

        return jsonify({
            "error": "Could not update student. Check for duplicate IDs or invalid data."
        }), 400

    finally:
        conn.close()


# DELETE: Remove a student by database ID
@app.route('/api/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    conn = get_db_connection()

    try:
        cursor = conn.execute(
            'DELETE FROM students WHERE id = ?',
            (id,)
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Student not found"
            }), 404

        return jsonify({
            "message": "Student deleted successfully"
        })

    finally:
        conn.close()


# Additional task: Get students by section
@app.route('/students/section/<section>')
def get_students_by_section(section):
    conn = get_db_connection()

    students = conn.execute(
        'SELECT * FROM students WHERE section = ?',
        (section,)
    ).fetchall()

    conn.close()

    return jsonify([dict(student) for student in students])


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
