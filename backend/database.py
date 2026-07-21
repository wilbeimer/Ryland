import json
import sqlite3
import os

from models import Assignment, Course, Quiz, Week

DATABASE_URL = os.getenv("DATABASE_URL", "backend/data/curriculum.db")


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
            duration_weeks INTEGER,
            hours_per_week INTEGER,
            weeks_data TEXT DEFAULT '[]',
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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id TEXT PRIMARY KEY,
            courseId TEXT NOT NULL,
            weekId TEXT,
            week INTEGER,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            questions TEXT NOT NULL,
            dueDate TEXT,
            points REAL,
            FOREIGN KEY (courseId) REFERENCES courses(id),
            FOREIGN KEY (weekId) REFERENCES course_weeks(id)
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


def _save_course_row(cur, course: Course):
    cur.execute(
        """
        UPDATE courses
        SET status = ?,
            description = ?,
            domain = ?,
            subdomains = ?,
            prerequisites = ?,
            duration_weeks = ?,
            hours_per_week = ?,
            textbook = ?
        WHERE id = ?
        """,
        (
            course.status.value,
            course.description,
            course.domain,
            json.dumps(course.subdomains),
            json.dumps(course.prerequisites),
            course.duration_weeks,
            course.hours_per_week,
            (
                json.dumps(course.textbook.model_dump(mode="json"))
                if course.textbook
                else None
            ),
            course.id,
        ),
    )


def _clear_course_children(cur, course_id: str):
    cur.execute("DELETE FROM assignments WHERE courseId = ?", (course_id,))
    cur.execute("DELETE FROM quizzes WHERE courseId = ?", (course_id,))
    cur.execute("DELETE FROM course_weeks WHERE courseId = ?", (course_id,))


def _save_week(cur, course_id: str, week: Week):
    cur.execute(
        """
        INSERT INTO course_weeks (id, courseId, week, goal, topics)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            week.id,
            course_id,
            week.number,
            week.goal,
            json.dumps(week.topics),
        ),
    )


def _save_assignment(cur, course_id: str, week: Week, assignment: Assignment):
    cur.execute(
        """
        INSERT INTO assignments
            (id, courseId, weekId, week, title, type, description,
             requirements, dueDate, points, rubric, resources)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            assignment.id,
            course_id,
            week.id,
            week.number,
            assignment.title,
            assignment.type.value,
            assignment.description,
            json.dumps(assignment.requirements),
            assignment.dueDate,
            assignment.points,
            assignment.rubric,
            json.dumps([r.model_dump(mode="json") for r in assignment.resources]),
        ),
    )


def _save_quiz(cur, course_id: str, week: Week, quiz: Quiz):
    cur.execute(
        """
        INSERT INTO quizzes
            (id, courseId, weekId, week, title, type, questions, dueDate, points)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            quiz.id,
            course_id,
            week.id,
            week.number,
            quiz.title,
            quiz.type.value,
            json.dumps([q.model_dump(mode="json") for q in quiz.questions]),
            quiz.dueDate,
            quiz.points,
        ),
    )


def save_course(course: Course):
    with sqlite3.connect(DATABASE_URL, check_same_thread=False, timeout=30) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        _save_course_row(cur, course)
        _clear_course_children(cur, course.id)

        for week in course.weeks:
            _save_week(cur, course.id, week)
            for assignment in week.assignments:
                _save_assignment(cur, course.id, week, assignment)
            if week.quiz:
                _save_quiz(cur, course.id, week, week.quiz)

        conn.commit()


def save_course_status(course: Course):
    with sqlite3.connect(DATABASE_URL, check_same_thread=False, timeout=30) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            "UPDATE courses SET status = ? WHERE id = ?",
            (course.status.value, course.id),
        )
        conn.commit()
