import sqlite3
import os

DATABASE_URL = os.getenv("DATABASE_URL", "curriculum.db")


def init_db(database: str = DATABASE_URL):
    print("initializing db...")
    conn = sqlite3.connect(database)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            color TEXT,
            domain TEXT,
            subdomains TEXT,
            prerequisites TEXT,
            weeks INTEGER,
            hours_per_week INTEGER,
            status TEXT DEFAULT 'pending',
            textbook TEXT DEFAULT '{}'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS course_weeks (
            id TEXT PRIMARY KEY,
            courseId TEXT NOT NULL,
            week INTEGER NOT NULL,
            goal TEXT,
            topics TEXT,
            FOREIGN KEY (courseId) REFERENCES courses(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id TEXT PRIMARY KEY,
            courseId TEXT NOT NULL,
            weekId TEXT,
            week INTEGER,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            requirements TEXT,
            dueDate TEXT,
            points REAL,
            rubric TEXT,
            resources TEXT DEFAULT '[]',
            FOREIGN KEY (courseId) REFERENCES courses(id),
            FOREIGN KEY (weekId) REFERENCES course_weeks(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id TEXT PRIMARY KEY,
            assignmentId TEXT NOT NULL,
            grade REAL,
            feedback TEXT,
            content TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (assignmentId) REFERENCES assignments(id)
        )
    """)

    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DATABASE_URL, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
