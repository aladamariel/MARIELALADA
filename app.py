
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to my first API! \n" \
           "This is a simple API built with flask. \n" \
           "You can test it by visiting /student."

@app.route('/student')
def get_student():
    return jsonify({
        "student_id": "24-00357",
        "name": "Mariel Alada",
        "program": "BSIT",
        "year": 3,
        "section": "A"
    })

@app.route('/hello')
def say_hello():
    name = request.args.get('name', 'Student')
    return jsonify({
        "message": f"Hello, {name}!"
    })

@app.route('/attendance')
def get_attendance():
    return jsonify({
        "student_name": "Mariel Alada",
        "attendance_status": "Present",
        "attendance_percentage": 95
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
