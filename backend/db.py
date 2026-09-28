from contextlib import contextmanager
import sqlite3
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException
from pydantic import SecretStr

from backend.models import Course, User, Week

DB_PATH = Path(__file__).parent / "courses.db"


class InvalidCourseError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class InvalidWeekError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class InvalidUserError(Exception):
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
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS User (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                password TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS Course (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (user_id) REFERENCES User(id)
            );
            CREATE TABLE IF NOT EXISTS Week (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                week_number INTEGER NOT NULL,
                description TEXT,
                FOREIGN KEY (course_id) REFERENCES Course(id)
            );
            """
        )


# USERS
def get_user_by_id(id: str):
    with get_conn() as conn:
        row = conn.execute(
            """
                SELECT *
                FROM User
                WHERE id=?
            """,
            (id,)
        ).fetchone()

        if not row:
            raise HTTPException(401, "Couldn't identify the user")

        user = User.model_validate(dict(row))
    return user


def add_user_to_db(user: User):
    try:
        with get_conn() as conn:
            conn.execute(
                """
                    INSERT OR IGNORE INTO User
                    (id, email, password)
                    VALUES (?, ?, ?)
                """,
                (str(user.id), user.email, user.password.get_secret_value())
            )
        return str(user.id)
    except sqlite3.IntegrityError as e:
        raise InvalidUserError(message="Invalid user details provided") from e


# COURSES
def add_course_to_db(course: Course):
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO Course (id, user_id, name, description) VALUES (?, ?, ?, ?)",
                (str(course.id), str(course.user_id), course.name, course.desc)
            )
        return str(course.id)
    except sqlite3.IntegrityError as e:
        raise InvalidCourseError(message="Invalid course details provided") from e


def get_courses(user_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, name
            FROM Course
            WHERE user_id=?
            """,
            (user_id,)
        ).fetchall()
    return [dict(row) for row in rows]


# WEEKS
def add_week_to_db(week: Week):
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO Week (id, course_id, week_number, description) VALUES (?, ?, ?, ?)",
                (str(week.id), str(week.course_id), week.week_number, week.desc)
            )
        return str(week.id)
    except sqlite3.IntegrityError as e:
        raise InvalidWeekError(message="Invalid week details provided") from e


def get_weeks(course_id) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, course_id, week_number, description
            FROM Week
            WHERE course_id=?
            ORDER BY week_number
            """,
            (str(course_id),)
        ).fetchall()
    return [dict(row) for row in rows]


if __name__ == "__main__":
    init_db()
    dev_user = User(id=UUID("00000000-0000-0000-0000-000000000001"), email="test@gmail.com", password=SecretStr("password"))
    add_user_to_db(dev_user)
