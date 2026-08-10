"""Tests for the Topic REST API.

Topics are nested under subjects, so the tests create a subject first
and clean it up afterwards. Runs against the isolated "bytebrains_test"
database (see conftest.py).
"""

import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_name() -> str:
    return f"Test Topic {uuid.uuid4().hex[:8]}"


def _create_subject() -> dict:
    response = client.post(
        "/api/subjects",
        json={"name": f"Test Subject {uuid.uuid4().hex[:8]}"},
    )
    assert response.status_code == 201
    return response.json()


def _create_topic(subject_id: str, name: str) -> dict:
    response = client.post(
        f"/api/subjects/{subject_id}/topics",
        json={"name": name, "description": "Test description"},
    )
    assert response.status_code == 201
    return response.json()


def test_list_topics_returns_list() -> None:
    subject = _create_subject()
    response = client.get(f"/api/subjects/{subject['id']}/topics")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    client.delete(f"/api/subjects/{subject['id']}")


def test_create_topic() -> None:
    subject = _create_subject()
    name = _unique_name()
    response = client.post(
        f"/api/subjects/{subject['id']}/topics",
        json={"name": name, "description": "Learn joins"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == name
    assert body["description"] == "Learn joins"
    assert body["subject_id"] == subject["id"]
    assert body["order_index"] == 0
    assert body["id"]
    assert body["created_at"]

    client.delete(f"/api/subjects/{subject['id']}")


def test_list_includes_created_topic() -> None:
    subject = _create_subject()
    name = _unique_name()
    created = _create_topic(subject["id"], name)

    response = client.get(f"/api/subjects/{subject['id']}/topics")
    assert response.status_code == 200
    names = [topic["name"] for topic in response.json()]
    assert name in names

    client.delete(f"/api/subjects/{subject['id']}")


def test_get_topic_by_id() -> None:
    subject = _create_subject()
    name = _unique_name()
    created = _create_topic(subject["id"], name)

    response = client.get(
        f"/api/subjects/{subject['id']}/topics/{created['id']}"
    )
    assert response.status_code == 200
    assert response.json()["name"] == name

    client.delete(f"/api/subjects/{subject['id']}")


def test_get_missing_topic_returns_404() -> None:
    subject = _create_subject()
    response = client.get(
        f"/api/subjects/{subject['id']}/topics/{uuid.uuid4()}"
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Topic not found"}
    client.delete(f"/api/subjects/{subject['id']}")


def test_topic_of_other_subject_returns_404() -> None:
    subject_a = _create_subject()
    subject_b = _create_subject()
    created = _create_topic(subject_a["id"], _unique_name())

    response = client.get(
        f"/api/subjects/{subject_b['id']}/topics/{created['id']}"
    )
    assert response.status_code == 404

    client.delete(f"/api/subjects/{subject_a['id']}")
    client.delete(f"/api/subjects/{subject_b['id']}")


def test_create_topic_for_missing_subject_returns_404() -> None:
    response = client.post(
        f"/api/subjects/{uuid.uuid4()}/topics",
        json={"name": _unique_name()},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Subject not found"}


def test_list_topics_for_missing_subject_returns_404() -> None:
    response = client.get(f"/api/subjects/{uuid.uuid4()}/topics")
    assert response.status_code == 404


def test_update_topic() -> None:
    subject = _create_subject()
    created = _create_topic(subject["id"], _unique_name())

    response = client.put(
        f"/api/subjects/{subject['id']}/topics/{created['id']}",
        json={"name": "Renamed Topic", "order_index": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Renamed Topic"
    assert body["order_index"] == 5

    client.delete(f"/api/subjects/{subject['id']}")


def test_update_missing_topic_returns_404() -> None:
    subject = _create_subject()
    response = client.put(
        f"/api/subjects/{subject['id']}/topics/{uuid.uuid4()}",
        json={"name": "Whatever"},
    )
    assert response.status_code == 404
    client.delete(f"/api/subjects/{subject['id']}")


def test_delete_topic() -> None:
    subject = _create_subject()
    created = _create_topic(subject["id"], _unique_name())

    response = client.delete(
        f"/api/subjects/{subject['id']}/topics/{created['id']}"
    )
    assert response.status_code == 204

    client.delete(f"/api/subjects/{subject['id']}")


def test_get_after_delete_returns_404() -> None:
    subject = _create_subject()
    created = _create_topic(subject["id"], _unique_name())
    client.delete(f"/api/subjects/{subject['id']}/topics/{created['id']}")

    response = client.get(
        f"/api/subjects/{subject['id']}/topics/{created['id']}"
    )
    assert response.status_code == 404

    client.delete(f"/api/subjects/{subject['id']}")


def test_order_index_auto_increments() -> None:
    subject = _create_subject()
    first = _create_topic(subject["id"], _unique_name())
    second = _create_topic(subject["id"], _unique_name())
    assert first["order_index"] == 0
    assert second["order_index"] == 1
    client.delete(f"/api/subjects/{subject['id']}")


def test_invalid_uuid_returns_422() -> None:
    response = client.get("/api/subjects/not-a-uuid/topics")
    assert response.status_code == 422
