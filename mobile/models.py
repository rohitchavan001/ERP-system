import os
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "library.db")
os.makedirs(DATA_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
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

def compute_expiry(admission_date_str, duration_months):
    try:
        dt = datetime.strptime(admission_date_str, "%Y-%m-%d")
        exp = dt + relativedelta(months=int(duration_months or 0))
        return exp.strftime("%Y-%m-%d")
    except Exception:
        return admission_date_str

def add_student(student):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO students
        (first_name, middle_name, surname, name, mobile, parents_mobile, email,
         aadhaar_no, address, course, gender, date_of_birth, admission_date,
         duration_months, expiry_date, fees_paid, aadhaar_image, application_for)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student.get("first_name"),
        student.get("middle_name"),
        student.get("surname"),
        student["name"],
        student["mobile"],
        student.get("parents_mobile"),
        student.get("email"),
        student.get("aadhaar_no"),
        student.get("address"),
        student.get("course"),
        student.get("gender"),
        student.get("date_of_birth"),
        student.get("admission_date"),
        student.get("duration_months"),
        student.get("expiry_date"),
        float(student.get("fees_paid") or 0),
        student.get("aadhaar_image"),
        student.get("application_for"),
    ))
    conn.commit()
    conn.close()

def list_students():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, mobile, course, expiry_date, aadhaar_image FROM students ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "name": r[1],
            "mobile": r[2],
            "course": r[3],
            "expiry": r[4],
            "aadhaar_image": r[5],
        }
        for r in rows
    ]
