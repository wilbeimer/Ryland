"""Focused coverage for calendar weeks grouped by due_date."""

import sqlite3
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.db import (
    add_assignment_to_db,
    add_course_to_db,
    add_user_to_db,
    add_week_to_db,
    init_db,
)
from backend.endpoints import app
from backend.models import Assignment, AssignmentType, Course, User, Week

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
        yield test_client


def test_calendar_weeks_group_by_due_date_not_week_number(client):
    course_a = uuid4()
    course_b = uuid4()
    week_a1 = uuid4()
    week_b2 = uuid4()
    add_course_to_db(
        Course(
            id=course_a,
            user_id=SEEDED_USER,
            name="Algebra",
            description="A",
            color="#e5446d",
            start_date=date(2026, 3, 2),
        )
    )
    add_course_to_db(
        Course(
            id=course_b,
            user_id=SEEDED_USER,
            name="Biology",
            description="B",
            color="#0d7377",
            start_date=date(2026, 2, 23),
        )
    )
    add_week_to_db(
        Week(id=week_a1, course_id=course_a, week_number=1, description="Alg 1")
    )
    # Different course week_number, same calendar week via due_date.
    add_week_to_db(
        Week(id=week_b2, course_id=course_b, week_number=2, description="Bio 2")
    )

    ny = ZoneInfo("America/New_York")
    add_assignment_to_db(
        Assignment(
            id=uuid4(),
            week_id=week_a1,
            type=AssignmentType.TEXT,
            name="Alg essay",
            description="Write",
            rubric={"score": 1},
            due_date=datetime(2026, 3, 4, 23, 59, tzinfo=ny),
        )
    )
    add_assignment_to_db(
        Assignment(
            id=uuid4(),
            week_id=week_b2,
            type=AssignmentType.QUIZ,
            name="Bio quiz",
            description="Quiz",
            rubric={"score": 1},
            # Same ISO week (Mon 2026-03-02); UTC instant whose NY day is Wed.
            due_date=datetime(2026, 3, 5, 3, 0, tzinfo=UTC),
        )
    )
    add_assignment_to_db(
        Assignment(
            id=uuid4(),
            week_id=week_a1,
            type=AssignmentType.TEXT,
            name="Next week",
            description="Later",
            rubric={"score": 1},
            due_date=datetime(2026, 3, 4, 23, 59, tzinfo=ny) + timedelta(days=7),
        )
    )

    response = client.get("/calendar/weeks")
    assert response.status_code == 200
    weeks = response.json()
    assert len(weeks) == 2
    assert weeks[0]["start_date"] == "2026-03-02"
    assert weeks[0]["end_date"] == "2026-03-08"
    names = {item["name"] for item in weeks[0]["assignments"]}
    assert names == {"Alg essay", "Bio quiz"}
    colors = {item["course_color"] for item in weeks[0]["assignments"]}
    assert colors == {"#e5446d", "#0d7377"}
    assert weeks[1]["start_date"] == "2026-03-09"
    assert weeks[1]["assignments"][0]["name"] == "Next week"
