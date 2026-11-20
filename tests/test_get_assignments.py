import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from pydantic import SecretStr

from backend.db import (
    add_assignment_to_db,
    add_course_to_db,
    add_user_to_db,
    add_week_to_db,
    get_assignments,
    init_db,
)
from backend.models import Assignment, AssignmentType, Course, User, Week

SEEDED_USER = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def db(tmp_path, monkeypatch):
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
    return database


def test_get_assignments_orders_text_before_quiz_then_by_due_date(db):
    course_id = uuid4()
    week_id = uuid4()
    base = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)

    add_course_to_db(
        Course(
            id=course_id,
            user_id=SEEDED_USER,
            name="Ordering Course",
            description="Assignments ordered for display",
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

    # Insert out of display order: quiz first, then later text, then earlier text.
    # Quiz has an earlier due date than both texts so type ordering must win.
    add_assignment_to_db(
        Assignment(
            id=uuid4(),
            week_id=week_id,
            type=AssignmentType.QUIZ,
            name="Week quiz",
            description="Post-learning quiz",
            rubric={"criteria": []},
            due_date=base + timedelta(days=1),
        )
    )
    add_assignment_to_db(
        Assignment(
            id=uuid4(),
            week_id=week_id,
            type=AssignmentType.TEXT,
            name="Later text",
            description="Second text assignment",
            rubric={"criteria": []},
            due_date=base + timedelta(days=5),
        )
    )
    add_assignment_to_db(
        Assignment(
            id=uuid4(),
            week_id=week_id,
            type=AssignmentType.TEXT,
            name="Earlier text",
            description="First text assignment",
            rubric={"criteria": []},
            due_date=base + timedelta(days=3),
        )
    )
    add_assignment_to_db(
        Assignment(
            id=uuid4(),
            week_id=week_id,
            type=AssignmentType.QUIZ,
            name="Later quiz",
            description="Second quiz",
            rubric={"criteria": []},
            due_date=base + timedelta(days=7),
        )
    )

    assignments = get_assignments(week_id)
    names = [a["name"] for a in assignments]
    types = [a["type"] for a in assignments]

    assert names == ["Earlier text", "Later text", "Week quiz", "Later quiz"]
    assert types == ["text", "text", "quiz", "quiz"]
