import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.db import (
    add_assignment_to_db,
    add_course_to_db,
    add_quiz_to_db,
    add_user_to_db,
    add_week_to_db,
    init_db,
)
from backend.endpoints import app
from backend.models import (
    Assignment,
    AssignmentType,
    Course,
    QuestionType,
    Quiz,
    QuizQuestion,
    User,
    Week,
)

SEEDED_USER = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def client(tmp_path, monkeypatch):
    database = tmp_path / "curriculum.db"

    @contextmanager
    def get_conn(path=database):
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.commit()
            conn.close()

    monkeypatch.setattr("backend.db.get_conn", get_conn)
    init_db()
    add_user_to_db(
        User(
            id=SEEDED_USER,
            email="test@mail.com",
            password=SecretStr("password"),
        )
    )

    with TestClient(app) as test_client:
        yield test_client, database


def test_delete_course_removes_weeks_assignments_and_quizzes(client):
    test_client, database = client
    course_id = uuid4()
    week_id = uuid4()
    assignment_id = uuid4()
    quiz_id = uuid4()

    add_course_to_db(
        Course(
            id=course_id,
            user_id=SEEDED_USER,
            name="Temp Course",
            description="Will be deleted",
        )
    )
    add_week_to_db(
        Week(
            id=week_id,
            course_id=course_id,
            week_number=1,
            description="Week one",
        )
    )
    add_assignment_to_db(
        Assignment(
            id=assignment_id,
            week_id=week_id,
            type=AssignmentType.QUIZ,
            name="Quiz one",
            description="A quiz",
            rubric={"score": 10},
            due_date=datetime.now(UTC) + timedelta(days=3),
        )
    )
    add_quiz_to_db(
        Quiz(
            id=quiz_id,
            assignment_id=assignment_id,
            time_limit=timedelta(minutes=10),
            questions=[
                QuizQuestion(
                    question_type=QuestionType.SHORT,
                    prompt="What is 2+2?",
                    options=None,
                    correct_answer="4",
                )
            ],
        )
    )

    response = test_client.delete(f"/courses/{course_id}")
    assert response.status_code == 204

    listed = test_client.get("/courses")
    assert listed.status_code == 200
    assert listed.json() == []

    with sqlite3.connect(database) as conn:
        assert conn.execute("SELECT COUNT(*) FROM Course").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM Week").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM Assignment").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM Quiz").fetchone()[0] == 0


def test_delete_course_unknown_returns_404(client):
    test_client, _database = client
    response = test_client.delete(f"/courses/{uuid4()}")
    assert response.status_code == 404


def test_delete_other_users_course_returns_404_and_leaves_it(client):
    test_client, database = client
    other_user = uuid4()
    course_id = uuid4()

    add_user_to_db(
        User(
            id=other_user,
            email="other@mail.com",
            password=SecretStr("password"),
        )
    )
    add_course_to_db(
        Course(
            id=course_id,
            user_id=other_user,
            name="Other Course",
            description="Not yours",
        )
    )

    response = test_client.delete(f"/courses/{course_id}")
    assert response.status_code == 404

    with sqlite3.connect(database) as conn:
        row = conn.execute(
            "SELECT id, user_id FROM Course WHERE id=?",
            (str(course_id),),
        ).fetchone()
        assert row is not None
        assert row[1] == str(other_user)


def test_delete_course_blocked_while_generation_active(client):
    test_client, database = client
    from backend import endpoints
    from backend.endpoints import GenerationJob

    course_id = uuid4()
    add_course_to_db(
        Course(
            id=course_id,
            user_id=SEEDED_USER,
            name="Building",
            description="Still generating",
        )
    )

    job = GenerationJob(
        job_id=uuid4(),
        user_id=SEEDED_USER,
        status="running",
        course_id=course_id,
    )
    endpoints._jobs[job.job_id] = job

    try:
        response = test_client.delete(f"/courses/{course_id}")
        assert response.status_code == 409

        with sqlite3.connect(database) as conn:
            assert (
                conn.execute(
                    "SELECT COUNT(*) FROM Course WHERE id=?",
                    (str(course_id),),
                ).fetchone()[0]
                == 1
            )
    finally:
        endpoints._jobs.pop(job.job_id, None)
        job.worker_done.set()
