import sqlite3

conn = sqlite3.connect("students.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    name TEXT NOT NULL,
    program TEXT NOT NULL,
    year INTEGER NOT NULL,
    section TEXT NOT NULL
)
""")

# Clear previous sample records
cursor.execute("DELETE FROM students")

# Five sample student records
students = [
    ("2026-00123", "Juan Dela Cruz", "BSIT", 1, "A"),
    ("2026-00124", "Maria Santos", "BSIT", 1, "A"),
    ("2026-00125", "Pedro Reyes", "BSIT", 1, "B"),
    ("2026-00126", "Ana Garcia", "BSCS", 2, "A"),
    ("2026-00127", "Mark Ramos", "BSIT", 3, "B")
]

cursor.executemany("""
INSERT INTO students (student_id, name, program, year, section)
VALUES (?, ?, ?, ?, ?)
""", students)

conn.commit()
conn.close()

print("Database created successfully.")