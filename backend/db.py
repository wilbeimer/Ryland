from contextlib import contextmanager
import sqlite3
from uuid import uuid4
from pathlib import Path

from backend.models import Course

DB_PATH = Path(__file__).parent / "courses.db"


class InvalidCourseError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


@contextmanager
def get_conn(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS courses (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT
            )
            """
        )


def create_course(course: Course):
    course_id = str(uuid4())
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO courses (id, name, description) VALUES (?, ?, ?)",
                (course_id, course.name, course.desc)
            )
        return course_id
    except sqlite3.IntegrityError as e:
        raise InvalidCourseError(message="Invalid course details provided") from e


def get_courses() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name FROM courses").fetchall()
    return [dict(row) for row in rows]
