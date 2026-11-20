"""Focused coverage for course color, start_date, and derived week dates."""

import sqlite3
from contextlib import contextmanager
from datetime import UTC, date, datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.course_dates import due_datetime_for_assignment
from backend.db import add_course_to_db, add_user_to_db, add_week_to_db, init_db
from backend.endpoints import app
from backend.models import Course, User, Week

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


def test_course_color_patch_and_week_date_range(client):
    course_id = uuid4()
    week_id = uuid4()
    add_course_to_db(
        Course(
            id=course_id,
            user_id=SEEDED_USER,
            name="Dated Course",
            description="Has a start date",
            color="#e5446d",
            start_date=date(2026, 3, 2),
        )
    )
    add_week_to_db(
        Week(
            id=week_id,
            course_id=course_id,
            week_number=2,
            description="Second week",
        )
    )

    patched = client.patch(
        f"/courses/{course_id}",
        json={"color": "#0d7377"},
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["color"] == "#0d7377"
    assert body["start_date"] == "2026-03-02"

    weeks = client.get(f"/courses/{course_id}/weeks")
    assert weeks.status_code == 200
    week = weeks.json()[0]
    assert week["week_number"] == 2
    assert week["start_date"] == "2026-03-09"
    assert week["end_date"] == "2026-03-15"


def test_due_datetime_uses_learner_timezone():
    """UTC instant on week start can be the prior local day; fallback stays tz-aware."""
    tz = ZoneInfo("America/New_York")
    start = date(2026, 3, 2)
    # 2026-03-02T01:00Z == 2026-03-01T20:00 America/New_York (before week start).
    provided = datetime(2026, 3, 2, 1, 0, tzinfo=UTC)
    result = due_datetime_for_assignment(start, 1, "text", provided, tz=tz)
    assert result == datetime(2026, 3, 6, 23, 59, tzinfo=tz)
    assert result.tzinfo is not None
