from contextlib import contextmanager
import sqlite3
from pathlib import Path
from uuid import UUID
import json

from fastapi import HTTPException

from backend.models import Assignment, Course, User, Week

DB_PATH = Path(__file__).parent / "courses.db"


class InvalidCourseError(Exception):
    pass


class InvalidWeekError(Exception):
    pass


class DuplicateWeekError(InvalidWeekError):
    pass


class InvalidAssignmentError(Exception):
    pass


class InvalidUserError(Exception):
    pass


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
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS Course (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL CHECK (length(trim(name)) > 0),
                description TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_course_user ON Course(user_id);

            CREATE TABLE IF NOT EXISTS Week (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                week_number INTEGER NOT NULL CHECK (week_number >= 1),
                description TEXT NOT NULL,
                UNIQUE (course_id, week_number),
                FOREIGN KEY (course_id) REFERENCES Course(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS Assignment (
                id TEXT PRIMARY KEY,
                week_id TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('text', 'quiz')),
                name TEXT NOT NULL CHECK (length(trim(name)) > 0),
                description TEXT NOT NULL,
                rubric TEXT NOT NULL CHECK (json_valid(rubric)),
                due_date TEXT NOT NULL CHECK (julianday(due_date) IS NOT NULL),
                FOREIGN KEY (week_id) REFERENCES Week(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_assignment_week ON Assignment(week_id);
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
        raise InvalidUserError("Invalid user details provided") from e


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
        raise InvalidCourseError("Invalid course details provided") from e


def get_courses(user_id: UUID) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, name
            FROM Course
            WHERE user_id=?
            """,
            (str(user_id),)
        ).fetchall()
    return [dict(row) for row in rows]


# WEEKS
def add_week_to_db(week: Week) -> str:
    try:
        with get_conn() as conn:
            conn.execute(
                """
                INSERT
                INTO Week (id,
                           course_id,
                           week_number,
                           description)
                VALUES (?, ?, ?, ?)
                """,
                (
                    str(week.id),
                    str(week.course_id),
                    week.week_number,
                    week.desc)
            )
        return str(week.id)
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE":
            raise DuplicateWeekError("A week with this number already exists in the course") from e
        raise InvalidWeekError("Invalid week data provided") from e


def get_weeks(course_id: UUID) -> list[dict]:
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


# ASSIGNMENTS
def add_assignment_to_db(assignment: Assignment) -> str:
    try:
        with get_conn() as conn:
            conn.execute(
                """
                INSERT
                INTO Assignment (id,
                                week_id,
                                type,
                                name,
                                description,
                                rubric,
                                due_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(assignment.id),
                    str(assignment.week_id),
                    assignment.type.value,
                    assignment.name,
                    assignment.desc,
                    json.dumps(assignment.rubric),
                    assignment.due_date.isoformat()
                )
            )
            return str(assignment.id)
    except sqlite3.IntegrityError as e:
        raise InvalidAssignmentError("Invalid data for assignment") from e


def get_assignments(course_id: UUID, week_id: UUID) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT a.id, a.type, a.name, a.description, a.rubric, a.due_date
            FROM Assignment a JOIN Week w
            ON a.week_id = w.id
            WHERE w.course_id=?
            AND a.week_id=?
            """,
            (str(course_id), str(week_id))
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["rubric"] = json.loads(item["rubric"])
            result.append(item)
    return result


if __name__ == "__main__":
    init_db()
