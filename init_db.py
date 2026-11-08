
import sqlite3

DATABASE = "students.db"


def initialize_database():
    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year INTEGER NOT NULL,
            section TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'Local'
        )
    """)

    # Add source column if the database already exists
    columns = conn.execute(
        "PRAGMA table_info(students)"
    ).fetchall()

    column_names = [column[1] for column in columns]

    if "source" not in column_names:
        conn.execute("""
            ALTER TABLE students
            ADD COLUMN source TEXT NOT NULL DEFAULT 'Local'
        """)

    # Insert sample students only if the table is empty
    student_count = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    if student_count == 0:
        students = [
            (
                "24-00357",
                "Mariel Alada",
                "BSIT",
                3,
                "A",
                "Local"
            ),
            (
                "24-00358",
                "Juan Dela Cruz",
                "BSIT",
                3,
                "A",
                "Local"
            ),
            (
                "24-00359",
                "Maria Santos",
                "BSIT",
                3,
                "A",
                "Local"
            ),
            (
                "24-00360",
                "Pedro Reyes",
                "BSIT",
                3,
                "A",
                "Local"
            ),
            (
                "24-00361",
                "Ana Garcia",
                "BSIT",
                3,
                "A",
                "Local"
            )
        ]

        conn.executemany("""
            INSERT INTO students (
                student_id,
                name,
                program,
                year,
                section,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, students)

    conn.commit()
    conn.close()

    print("Database initialized successfully!")
    print("Student records are ready.")


if __name__ == "__main__":
    initialize_database()
