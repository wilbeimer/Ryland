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
