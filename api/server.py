import os
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

APP_DIR = os.path.join(os.environ.get("APPDATA", "."), "ERP_System")
os.makedirs(APP_DIR, exist_ok=True)
# Prefer project-root database in dev if present; otherwise use AppData
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEV_DB_PATH = os.path.join(PROJECT_ROOT, "library.db")
DB_PATH = DEV_DB_PATH if os.path.exists(DEV_DB_PATH) else os.path.join(APP_DIR, "library.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
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
        """
    )
    conn.commit()
    conn.close()

def compute_expiry(admission_date_str, duration_months):
    try:
        dt = datetime.strptime(admission_date_str, "%Y-%m-%d")
        exp = dt + relativedelta(months=int(duration_months or 0))
        return exp.strftime("%Y-%m-%d")
    except Exception:
        return admission_date_str

class StudentCreate(BaseModel):
    first_name: str | None = None
    middle_name: str | None = None
    surname: str | None = None
    name: str
    mobile: str
    parents_mobile: str | None = None
    email: str | None = None
    aadhaar_no: str | None = None
    address: str | None = None
    course: str | None = None
    gender: str | None = None
    date_of_birth: str | None = None
    admission_date: str
    duration_months: int = 0
    expiry_date: str | None = None
    fees_paid: float = 0.0
    aadhaar_image: str | None = None
    application_for: str | None = None

class StudentUpdate(BaseModel):
    name: str | None = None
    mobile: str | None = None
    course: str | None = None
    expiry_date: str | None = None
    duration_months: int | None = None
    fees_paid: float | None = None
    aadhaar_image: str | None = None
    address: str | None = None
    email: str | None = None
    parents_mobile: str | None = None

class RenewRequest(BaseModel):
    months: int

app = FastAPI(title="ERP System API", version="2.0")

# Enable CORS for mobile app connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local network access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

@app.get("/health")
def health():
    """Health check endpoint for mobile app connectivity"""
    return {
        "status": "ok",
        "db": DB_PATH,
        "version": "2.0",
        "message": "ERP System API is running"
    }

@app.get("/students")
def get_students():
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

@app.post("/students", status_code=201)
def create_student(s: StudentCreate):
    expiry = s.expiry_date or compute_expiry(s.admission_date, s.duration_months)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            """
            INSERT INTO students
            (first_name, middle_name, surname, name, mobile, parents_mobile, email,
             aadhaar_no, address, course, gender, date_of_birth, admission_date,
             duration_months, expiry_date, fees_paid, aadhaar_image, application_for)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                s.first_name,
                s.middle_name,
                s.surname,
                s.name,
                s.mobile,
                s.parents_mobile,
                s.email,
                s.aadhaar_no,
                s.address,
                s.course,
                s.gender,
                s.date_of_birth,
                s.admission_date,
                s.duration_months,
                expiry,
                float(s.fees_paid or 0),
                s.aadhaar_image,
                s.application_for,
            ),
        )
        conn.commit()
        new_id = c.lastrowid
        return {"id": new_id}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.put("/students/{student_id}")
def update_student(student_id: int, s: StudentUpdate):
    fields = []
    values = []
    for k, v in s.dict(exclude_unset=True).items():
        fields.append(f"{k}=?")
        values.append(v)
    if not fields:
        return {"updated": 0}
    values.append(student_id)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"UPDATE students SET {', '.join(fields)} WHERE id=?", values)
    conn.commit()
    conn.close()
    return {"updated": 1}

@app.post("/students/{student_id}/renew")
def renew_student(student_id: int, r: RenewRequest):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT admission_date, duration_months FROM students WHERE id=?", (student_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Not found")
    admission_date, duration_months = row
    new_duration = int(duration_months or 0) + int(r.months)
    new_expiry = compute_expiry(admission_date, new_duration)
    c.execute("UPDATE students SET duration_months=?, expiry_date=? WHERE id=?", (new_duration, new_expiry, student_id))
    conn.commit()
    conn.close()
    return {"expiry_date": new_expiry, "duration_months": new_duration}

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 ERP System API Server v2.0")
    print("=" * 60)
    print(f"📁 Database: {DB_PATH}")
    print(f"🌐 Server: http://0.0.0.0:8000")
    print(f"📱 Mobile: Connect using your PC's IP address")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
