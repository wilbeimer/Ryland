from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch

client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_get_nonexistent_course():
    response = client.get("/courses/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"detail": "Course not found"}


@patch("backend.main.generate_curriculum")
def test_get_courses(mock_generate):
    mock_generate.return_value = {}

    client.post(
        "/courses",
        json={
            "name": "Python",
            "color": "#3572A5"
        },
    )

    response = client.get("/courses")

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert "id" in body[0]
    assert body[0]["name"] == "Python"
    assert body[0]["color"] == "#3572A5"


@patch("backend.main.generate_curriculum")
def test_post_course(mock_generate):
    data = {"name": "Python", "color": "#3572A5"}

    response = client.post("/courses", json=data)

    assert response.status_code == 200
    body = response.json()

    assert "id" in body
    assert body["name"] == "Python"
    assert body["color"] == "#3572A5"
    assert body["status"] == "pending"

    mock_generate.assert_called_once()
