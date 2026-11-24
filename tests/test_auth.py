import re
import sqlite3
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from backend import db
from backend.auth import get_current_user
from backend.db import init_db
from backend.endpoints import app


@pytest.fixture
def client(tmp_path, monkeypatch, act_as_seed_user):
    database = tmp_path / "curriculum.db"

    @contextmanager
    def connect(path=database):
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.commit()
            conn.close()

    monkeypatch.setattr("backend.db.get_conn", connect)
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_FROM", raising=False)
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("RYLAND_DEV_SEED", raising=False)
    app.dependency_overrides.pop(get_current_user, None)
    init_db()

    with TestClient(app) as test_client:
        yield test_client


def _verification_token(capsys: pytest.CaptureFixture[str]) -> str:
    output = capsys.readouterr().out
    match = re.search(r"token=([^&\s]+)", output)
    assert match, output
    return match.group(1)


def test_signup_verify_and_signin(
    client: TestClient, capsys: pytest.CaptureFixture[str]
):
    signup = client.post(
        "/auth/signup",
        json={
            "username": "Ada",
            "password": "correct-horse",
            "email": "Ada@Example.com",
        },
    )
    assert signup.status_code == 201
    created = signup.json()
    assert created["username"] == "Ada"
    assert created["email"] == "ada@example.com"
    assert created["email_verified"] is False
    assert created["delivery"] == "logged"
    token = _verification_token(capsys)

    early = client.post(
        "/auth/signin",
        json={"username": "ada", "password": "correct-horse"},
    )
    assert early.status_code == 403

    bad = client.post("/auth/verify", json={"token": "not-a-real-token"})
    assert bad.status_code == 400

    verified = client.post("/auth/verify", json={"token": token})
    assert verified.status_code == 200
    assert verified.json()["email_verified"] is True
    again = client.post("/auth/verify", json={"token": token})
    assert again.status_code == 200

    wrong = client.post(
        "/auth/signin",
        json={"username": "ada", "password": "wrong-password-1"},
    )
    assert wrong.status_code == 401

    email_login = client.post(
        "/auth/signin",
        json={"username": "ada@example.com", "password": "correct-horse"},
    )
    assert email_login.status_code == 401

    signed = client.post(
        "/auth/signin",
        json={"username": "Ada", "password": "correct-horse"},
    )
    assert signed.status_code == 200
    payload = signed.json()
    assert payload["user"]["username"] == "Ada"
    assert payload["user"]["email_verified"] is True
    assert "password" not in payload["user"]
    session = payload["token"]

    anonymous = client.get("/courses")
    assert anonymous.status_code == 401
    courses = client.get("/courses", headers={"Authorization": f"Bearer {session}"})
    assert courses.status_code == 200
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {session}"})
    assert me.status_code == 200
    assert me.json()["email"] == "ada@example.com"

    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT password FROM User WHERE email = ?",
            ("ada@example.com",),
        ).fetchone()
    assert row is not None
    assert row["password"] != "correct-horse"
    assert row["password"].startswith("scrypt$")


def test_signup_rejects_duplicate_username_and_email(client: TestClient):
    first = client.post(
        "/auth/signup",
        json={
            "username": "grace",
            "password": "correct-horse",
            "email": "grace@example.com",
        },
    )
    assert first.status_code == 201

    duplicate_username = client.post(
        "/auth/signup",
        json={
            "username": "Grace",
            "password": "correct-horse",
            "email": "other@example.com",
        },
    )
    assert duplicate_username.status_code == 409

    duplicate_email = client.post(
        "/auth/signup",
        json={
            "username": "grace2",
            "password": "correct-horse",
            "email": "GRACE@example.com",
        },
    )
    assert duplicate_email.status_code == 409


def test_resend_and_resignup_after_expired_link(
    client: TestClient, capsys: pytest.CaptureFixture[str]
):
    body = {
        "username": "ada",
        "password": "correct-horse",
        "email": "ada@example.com",
    }
    created = client.post("/auth/signup", json=body)
    assert created.status_code == 201
    capsys.readouterr()

    resent = client.post(
        "/auth/resend",
        json={"username": "ada", "password": "correct-horse"},
    )
    assert resent.status_code == 200
    assert resent.json()["delivery"] == "logged"
    assert "token=" in capsys.readouterr().out
    blocked = client.post(
        "/auth/signup",
        json={**body, "password": "another-password"},
    )
    assert blocked.status_code == 409

    with db.get_conn() as conn:
        conn.execute(
            "UPDATE EmailVerification SET expires_at = ?",
            ("2000-01-01T00:00:00+00:00",),
        )
    replaced = client.post(
        "/auth/signup",
        json={**body, "password": "another-password"},
    )
    assert replaced.status_code == 201
    assert (
        client.post(
            "/auth/signin",
            json={"username": "ada", "password": "correct-horse"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/auth/signin",
            json={"username": "ada", "password": "another-password"},
        ).status_code
        == 403
    )


def test_seed_user_requires_dev_flag(tmp_path, monkeypatch):
    database = tmp_path / "curriculum.db"

    @contextmanager
    def connect(path=database):
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.commit()
            conn.close()

    monkeypatch.setattr("backend.db.get_conn", connect)
    monkeypatch.delenv("RYLAND_DEV_SEED", raising=False)
    db.ensure_seed_user()
    with connect() as conn:
        count = conn.execute("SELECT COUNT(*) AS n FROM User").fetchone()
    assert count is not None
    assert count["n"] == 0

    monkeypatch.setenv("RYLAND_DEV_SEED", "1")
    db.ensure_seed_user()
    with connect() as conn:
        row = conn.execute(
            "SELECT username, email_verified, password FROM User"
        ).fetchone()
    assert row is not None
    assert row["username"] == "test"
    assert row["email_verified"] == 1
    assert str(row["password"]).startswith("scrypt$")
