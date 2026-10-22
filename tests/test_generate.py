import sqlite3
import threading
import time
from contextlib import contextmanager
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from agent.agent_loop import (
    CONTEXT_FILE,
    Agent,
    AgentRunResult,
    learner_brief,
    run_generation,
)
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
        if last["status"] in {"succeeded", "incomplete", "failed"}:
            return last
        time.sleep(0.02)
    raise AssertionError(last)


def test_generate_polls_until_course_is_saved(client, monkeypatch):
    started = threading.Event()
    release = threading.Event()
    course_id = uuid4()

    def fake_run_generation(
        *, user_id, goal, level, time_available, timezone_name, on_progress=None
    ):
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
        return AgentRunResult(
            course_id=str(course_id), summary="Built SQL Joins", completed=True
        )

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


def test_turn_cap_after_create_course_is_incomplete(client, monkeypatch):
    course_id = uuid4()

    def fake_run_generation(
        *, user_id, goal, level, time_available, timezone_name, on_progress=None
    ):
        add_course_to_db(
            Course(
                id=course_id,
                user_id=user_id,
                name="Partial SQL",
                description=goal,
            )
        )
        return AgentRunResult(
            course_id=str(course_id),
            summary="Stopped mid-outline",
            completed=False,
        )

    monkeypatch.setattr("backend.endpoints.run_generation", fake_run_generation)
    created = client.post("/courses/generate", json=GENERATE_BODY)
    assert created.status_code == 202
    finished = wait_for_job(client, created.json()["job_id"])
    assert finished["status"] == "incomplete"
    assert finished["course_id"] == str(course_id)
    assert finished["course"]["name"] == "Partial SQL"
    assert "10-turn cap" in finished["detail"]
    assert "may be missing" in finished["detail"]
    assert "Stopped mid-outline" in finished["detail"]
    assert "10-turn cap" in finished["error"]


def test_second_build_is_rejected_while_one_is_running(client, monkeypatch):
    started = threading.Event()
    release = threading.Event()

    def fake_run_generation(**kwargs):
        on_progress = kwargs.get("on_progress")
        if on_progress:
            on_progress("Using create_course")
        started.set()
        assert release.wait(timeout=2)
        return AgentRunResult(course_id=None, summary="", completed=True)

    monkeypatch.setattr("backend.endpoints.run_generation", fake_run_generation)
    try:
        first = client.post("/courses/generate", json=GENERATE_BODY)
        assert first.status_code == 202
        job_id = first.json()["job_id"]
        assert started.wait(timeout=2)
        second = client.post("/courses/generate", json=GENERATE_BODY)
        assert second.status_code == 409
        assert job_id in second.json()["detail"]
    finally:
        release.set()

    assert wait_for_job(client, job_id)["status"] == "failed"
    third = client.post("/courses/generate", json=GENERATE_BODY)
    assert third.status_code == 202
    assert wait_for_job(client, third.json()["job_id"])["status"] == "failed"


def test_finished_jobs_expire(client, monkeypatch):
    def fake_run_generation(**kwargs):
        return AgentRunResult(course_id=None, summary="no course", completed=True)

    monkeypatch.setattr("backend.endpoints.run_generation", fake_run_generation)
    monkeypatch.setattr("backend.endpoints._MAX_FINISHED_JOBS", 1)
    first = client.post("/courses/generate", json=GENERATE_BODY)
    first_id = first.json()["job_id"]
    assert wait_for_job(client, first_id)["status"] == "failed"

    second = client.post("/courses/generate", json=GENERATE_BODY)
    second_id = second.json()["job_id"]
    assert wait_for_job(client, second_id)["status"] == "failed"

    # The next read evicts the oldest finished job once the cap is exceeded.
    assert client.get(f"/courses/generate/{first_id}").status_code == 404
    assert client.get(f"/courses/generate/{second_id}").status_code == 200

    monkeypatch.setattr("backend.endpoints._FINISHED_JOB_TTL_SECONDS", 0)
    assert client.get(f"/courses/generate/{second_id}").status_code == 404


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


def test_generate_rejects_invalid_timezone(client, monkeypatch):
    def fail_if_called(**kwargs):
        raise AssertionError("invalid timezone should not start a build")

    monkeypatch.setattr("backend.endpoints.run_generation", fail_if_called)
    response = client.post(
        "/courses/generate",
        json={**GENERATE_BODY, "timezone": "Eastern"},
    )
    assert response.status_code == 422
    assert "timezone" in response.text
    assert client.get("/courses").json() == []


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


def test_context_file_does_not_depend_on_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    agent = Agent(
        user_id=SEEDED_USER,
        client=object(),
        model="claude-haiku-4-5",
        context_file=CONTEXT_FILE,
    )
    assert CONTEXT_FILE.is_file()
    assert "course-building agent" in agent.system_prompt
