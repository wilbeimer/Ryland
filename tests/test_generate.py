import sqlite3
import threading
import time
from contextlib import contextmanager
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from agent.agent_loop import Agent, AgentRunResult, learner_brief, run_generation
from agent.tools import ask_user
from backend.db import add_course_to_db, add_user_to_db, init_db
from backend.endpoints import allowed_origins, app
from backend.models import Course, User

SEEDED_USER = UUID("00000000-0000-0000-0000-000000000001")

GENERATE_BODY = {
    "goal": "Learn SQL joins",
    "level": "beginner",
    "time_available": "4 hours a week for 3 weeks",
    "timezone": "America/New_York",
}


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
    from backend import endpoints

    endpoints._jobs.clear()
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


def wait_for_job(client: TestClient, job_id: str) -> dict:
    deadline = time.time() + 5
    last = None
    while time.time() < deadline:
        response = client.get(f"/courses/generate/{job_id}")
        assert response.status_code == 200
        last = response.json()
        if last["status"] in {"succeeded", "failed"}:
            return last
        time.sleep(0.02)
    raise AssertionError(last)


def test_generate_polls_until_course_is_saved(client, monkeypatch):
    started = threading.Event()
    release = threading.Event()
    course_id = uuid4()

    def fake_run_generation(*, user_id, goal, level, time_available, timezone_name, on_progress=None):
        assert goal == GENERATE_BODY["goal"]
        assert level == GENERATE_BODY["level"]
        assert time_available == GENERATE_BODY["time_available"]
        assert timezone_name == GENERATE_BODY["timezone"]
        if on_progress:
            on_progress("Using create_course")
        started.set()
        assert release.wait(timeout=2)
        add_course_to_db(
            Course(
                id=course_id,
                user_id=user_id,
                name="SQL Joins",
                description=goal,
            )
        )
        return AgentRunResult(course_id=str(course_id), summary="Built SQL Joins", completed=True)

    monkeypatch.setattr("backend.endpoints.run_generation", fake_run_generation)

    try:
        created = client.post("/courses/generate", json=GENERATE_BODY)
        assert created.status_code == 202
        body = created.json()
        assert body["status"] == "pending"
        assert body["course_id"] is None
        job_id = body["job_id"]
        assert created.headers["location"] == f"/courses/generate/{job_id}"

        assert started.wait(timeout=2)
        running = client.get(f"/courses/generate/{job_id}")
        assert running.status_code == 200
        assert running.json()["status"] == "running"
        assert running.json()["detail"] == "Using create_course"
        assert running.json()["course"] is None
    finally:
        release.set()

    finished = wait_for_job(client, job_id)
    assert finished["status"] == "succeeded"
    assert finished["error"] is None
    assert finished["course_id"] == str(course_id)
    assert finished["course"] == {
        "id": str(course_id),
        "name": "SQL Joins",
        "description": "Learn SQL joins",
    }
    assert finished["detail"] == "Built SQL Joins"

    listed = client.get("/courses")
    assert listed.status_code == 200
    assert any(item["id"] == str(course_id) for item in listed.json())


def test_generate_reports_failure_without_a_course(client, monkeypatch):
    def fake_run_generation(**kwargs):
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    monkeypatch.setattr("backend.endpoints.run_generation", fake_run_generation)
    created = client.post("/courses/generate", json=GENERATE_BODY)
    assert created.status_code == 202
    finished = wait_for_job(client, created.json()["job_id"])
    assert finished["status"] == "failed"
    assert finished["error"] == "ANTHROPIC_API_KEY is not set"
    assert finished["course_id"] is None
    assert client.get("/courses").json() == []


def test_generate_rejects_blank_fields(client):
    response = client.post(
        "/courses/generate",
        json={**GENERATE_BODY, "goal": "   "},
    )
    assert response.status_code == 422

    missing = client.post(
        "/courses/generate",
        json={"goal": "Learn SQL joins", "level": "beginner"},
    )
    assert missing.status_code == 422


def test_unknown_generation_job_is_not_found(client):
    response = client.get(f"/courses/generate/{uuid4()}")
    assert response.status_code == 404


def test_cors_preflight_allows_local_vite(client):
    origin = "http://localhost:5173"
    response = client.options(
        "/courses/generate",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin

    blocked = client.options(
        "/courses/generate",
        headers={
            "Origin": "http://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert blocked.headers.get("access-control-allow-origin") != "http://evil.example"


def test_allowed_origins_reads_env(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173, http://127.0.0.1:4173")
    assert allowed_origins() == ["http://localhost:5173", "http://127.0.0.1:4173"]

    monkeypatch.setenv("CORS_ORIGINS", "  ")
    assert allowed_origins() == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_learner_brief_includes_what_the_agent_asks_for():
    brief = learner_brief(
        goal="Learn SQL joins",
        level="beginner",
        time_available="4 hours a week for 3 weeks",
        timezone_name="America/New_York",
    )
    assert "Goal: Learn SQL joins" in brief
    assert "Level: beginner" in brief
    assert "Time available: 4 hours a week for 3 weeks" in brief
    assert "Timezone: America/New_York" in brief
    assert "Current date and time:" in brief
    assert "could not resolve" not in brief

    unknown = learner_brief(
        goal="Learn SQL joins",
        level="beginner",
        time_available="4 hours a week",
        timezone_name="not-a-timezone",
    )
    assert "not-a-timezone" in unknown
    assert "could not resolve timezone" in unknown


def test_run_generation_requires_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY is not set"):
        run_generation(
            user_id=SEEDED_USER,
            goal="Learn SQL joins",
            level="beginner",
            time_available="4 hours a week",
            timezone_name="UTC",
        )


def test_cli_agent_still_asks_on_the_terminal_by_default():
    agent = Agent(user_id=SEEDED_USER, client=object(), model="claude-haiku-4-5")
    assert agent.ask is ask_user
