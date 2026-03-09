import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "library.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Drop existing table if it exists to recreate with new schema
cursor.execute("DROP TABLE IF EXISTS students")

cursor.execute("""
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    middle_name TEXT,
    surname TEXT,
    name TEXT NOT NULL,
    mobile TEXT NOT NULL UNIQUE,
    parents_mobile TEXT,
    email TEXT,
    aadhaar_no TEXT,
    address TEXT,
    course TEXT,
    gender TEXT,
    date_of_birth TEXT,
    admission_date TEXT,
    duration_months INTEGER,
    expiry_date TEXT,
    fees_paid REAL DEFAULT 0,
    aadhaar_image TEXT,
    application_for TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("Database created/updated successfully with new schema.")








