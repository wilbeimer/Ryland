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
def test_post_course(mock_generate):
    data = {"name": "test_course_name", "color": "test_course_color"}

    response = client.post("/courses", json=data)

    assert response.status_code == 200
    body = response.json()

    assert "id" in body
    assert body["name"] == "test_course_name"
    assert body["color"] == "test_course_color"
    assert body["status"] == "pending"

    mock_generate.assert_called_once()
