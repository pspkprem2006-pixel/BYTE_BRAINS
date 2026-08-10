"""Tests for the Subject REST API.

Every test runs against the isolated "bytebrains_test" database (see
conftest.py). Subject names get a short random suffix so a previous
failed run can never cause an unexpected duplicate-name failure.
"""

import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_name() -> str:
    return f"Test Subject {uuid.uuid4().hex[:8]}"


def _create_subject(name: str, description: str = "Test description") -> None:
    response = client.post(
        "/api/subjects", json={"name": name, "description": description}
    )
    assert response.status_code == 201
    return response.json()


def test_list_subjects_returns_list() -> None:
    response = client.get("/api/subjects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_subject() -> None:
    name = _unique_name()
    response = client.post(
        "/api/subjects", json={"name": name, "description": "Learn databases"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == name
    assert body["description"] == "Learn databases"
    assert body["id"]
    assert body["user_id"]
    assert body["created_at"]

    client.delete(f"/api/subjects/{body['id']}")


def test_list_includes_created_subject() -> None:
    name = _unique_name()
    created = _create_subject(name)

    response = client.get("/api/subjects")
    assert response.status_code == 200
    names = [subject["name"] for subject in response.json()]
    assert name in names

    client.delete(f"/api/subjects/{created['id']}")


def test_get_subject_by_id() -> None:
    name = _unique_name()
    created = _create_subject(name)

    response = client.get(f"/api/subjects/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == name

    client.delete(f"/api/subjects/{created['id']}")


def test_get_missing_subject_returns_404() -> None:
    response = client.get(f"/api/subjects/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Subject not found"}


def test_update_subject() -> None:
    created = _create_subject(_unique_name())

    response = client.put(
        f"/api/subjects/{created['id']}",
        json={"name": "Renamed Subject", "description": "Updated description"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed Subject"
    assert response.json()["description"] == "Updated description"

    client.delete(f"/api/subjects/{created['id']}")


def test_update_missing_subject_returns_404() -> None:
    response = client.put(
        f"/api/subjects/{uuid.uuid4()}", json={"name": "Whatever"}
    )
    assert response.status_code == 404


def test_delete_subject() -> None:
    created = _create_subject(_unique_name())

    response = client.delete(f"/api/subjects/{created['id']}")
    assert response.status_code == 204


def test_get_after_delete_returns_404() -> None:
    created = _create_subject(_unique_name())
    client.delete(f"/api/subjects/{created['id']}")

    response = client.get(f"/api/subjects/{created['id']}")
    assert response.status_code == 404


def test_duplicate_subject_returns_409() -> None:
    name = _unique_name()
    created = _create_subject(name)

    response = client.post(
        "/api/subjects", json={"name": name, "description": "duplicate"}
    )
    assert response.status_code == 409
    assert response.json() == {"detail": "A subject with this name already exists"}

    client.delete(f"/api/subjects/{created['id']}")


def test_invalid_uuid_returns_422() -> None:
    response = client.get("/api/subjects/not-a-uuid")
    assert response.status_code == 422