import sqlite3


def init_db():
    conn = sqlite3.connect('curriculum.db')
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                color TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
                id TEXT PRIMARY KEY,
                courseId TEXT NOT NULL,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                dueDate TEXT,
                points REAL,
                content TEXT,
                rubric TEXT,
                FOREIGN KEY (courseId) REFERENCES courses(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
                id TEXT PRIMARY KEY,
                assignmentId TEXT NOT NULL,
                grade REAL,
                feedback TEXT,
                content TEXT NOT NULL,
                FOREIGN KEY (assignmentId) REFERENCES assignments(id)
        )
    """)
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect('curriculum.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
