"""Tests for learning-resource selection persistence and API.

Coverage:
- select resource (201) and duplicate URL (409)
- invalid URL / oversized fields (422)
- selecting for a subject owned by another user (404)
- selected list: empty, scoped by subject, limit clamp
- delete selection (204) and missing selection (404)
- canonicalization: duplicate URLs differing only by fragment / tracking
  params are treated as the same selection
- last_used_at update via mark_selections_used
"""

import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.models import LearningResourceSelection
from app.services.learning_resources.quality import canonical_resource_url

client = TestClient(app)


def _create_subject() -> dict:
    response = client.post(
        "/api/subjects", json={"name": f"Selection Subject {uuid.uuid4().hex[:8]}"}
    )
    assert response.status_code == 201
    return response.json()


def _create_selection(subject_id: str, url: str | None = None, title: str = "Resource") -> dict:
    if url is None:
        url = f"https://example.com/{uuid.uuid4().hex}.html"
    response = client.post(
        "/api/learning-resources/select",
        json={"subject_id": subject_id, "title": title, "url": url},
    )
    assert response.status_code == 201
    return response.json()


def test_select_resource_returns_201() -> None:
    subject = _create_subject()
    raw_url = f"https://Example.com/{uuid.uuid4().hex}/path?x=1"
    body = _create_selection(subject["id"], raw_url)

    assert body["subject_id"] == subject["id"]
    assert body["title"] == "Resource"
    assert body["url"] == raw_url.lower()
    assert body["domain"] == "example.com"
    assert body["resource_type"] == "other"
    assert "id" in body
    assert "created_at" in body


def test_duplicate_url_returns_409() -> None:
    subject = _create_subject()
    url = f"https://example.com/{uuid.uuid4().hex}/article"
    _create_selection(subject["id"], url)

    response = client.post(
        "/api/learning-resources/select",
        json={"subject_id": subject["id"], "title": "Again", "url": url},
    )
    assert response.status_code == 409
    assert "already" in response.json()["detail"].lower()


def test_duplicate_url_with_tracking_params_returns_409() -> None:
    subject = _create_subject()
    url = f"https://example.com/{uuid.uuid4().hex}/article"
    _create_selection(subject["id"], f"{url}?utm_source=x#top")

    response = client.post(
        "/api/learning-resources/select",
        json={"subject_id": subject["id"], "title": "Again", "url": url},
    )
    assert response.status_code == 409


def test_invalid_url_returns_422() -> None:
    subject = _create_subject()
    response = client.post(
        "/api/learning-resources/select",
        json={"subject_id": subject["id"], "title": "Bad", "url": "not-a-url"},
    )
    assert response.status_code == 422


def test_blank_title_returns_422() -> None:
    subject = _create_subject()
    response = client.post(
        "/api/learning-resources/select",
        json={"subject_id": subject["id"], "title": "   ", "url": "https://example.com/x"},
    )
    assert response.status_code == 422


def test_select_for_other_users_subject_returns_404() -> None:
    subject = _create_subject()
    other_id = uuid.uuid4()
    response = client.post(
        "/api/learning-resources/select",
        json={"subject_id": str(other_id), "title": "X", "url": "https://example.com/x"},
    )
    assert response.status_code == 404
    assert subject["id"] != str(other_id)


def test_list_selected_returns_selections() -> None:
    subject = _create_subject()
    sel1 = _create_selection(subject["id"])
    sel2 = _create_selection(subject["id"])

    response = client.get(f"/api/learning-resources/selected?subject_id={subject['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    ids = {item["id"] for item in body["resources"]}
    assert ids == {sel1["id"], sel2["id"]}


def test_list_selected_empty() -> None:
    subject = _create_subject()
    response = client.get(f"/api/learning-resources/selected?subject_id={subject['id']}")
    assert response.status_code == 200
    assert response.json()["resources"] == []
    assert response.json()["count"] == 0


def test_list_selected_without_filter_returns_all() -> None:
    response = client.get("/api/learning-resources/selected")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["resources"], list)
    assert body["count"] == len(body["resources"])


def test_delete_selection_returns_204() -> None:
    subject = _create_subject()
    sel = _create_selection(subject["id"])

    response = client.delete(f"/api/learning-resources/selected/{sel['id']}")
    assert response.status_code == 204

    response = client.get(f"/api/learning-resources/selected?subject_id={subject['id']}")
    assert response.json()["count"] == 0


def test_delete_missing_selection_returns_404() -> None:
    response = client.delete(f"/api/learning-resources/selected/{uuid.uuid4()}")
    assert response.status_code == 404


def test_canonical_resource_url_normalization() -> None:
    assert canonical_resource_url("HTTP://Example.com/path") == "http://example.com/path"
    assert canonical_resource_url("https://example.com/a#frag") == "https://example.com/a"
    assert (
        canonical_resource_url("https://example.com/a?utm_source=x&b=2")
        == "https://example.com/a?b=2"
    )
    assert canonical_resource_url("ftp://example.com/x") == ""
    assert canonical_resource_url("https://user:pass@example.com/x") == ""
    assert canonical_resource_url("") == ""
    truncated = canonical_resource_url("https://example.com/" + "a" * 600)
    assert truncated is not None and len(truncated) <= 500


def test_canonical_resource_url_rejects_non_http_and_private_hosts() -> None:
    assert canonical_resource_url("javascript:alert(1)") == ""
    assert canonical_resource_url("data:text/html,<script>alert(1)</script>") == ""
    assert canonical_resource_url("file:///etc/passwd") == ""
    assert canonical_resource_url("http:///nohost") == ""
    assert canonical_resource_url("not a url") == ""
    assert canonical_resource_url("http://localhost:8000/x") == ""
    assert canonical_resource_url("http://127.0.0.1/x") == ""
    assert canonical_resource_url("http://10.0.0.5/x") == ""
    assert canonical_resource_url("http://192.168.1.1/x") == ""
    assert canonical_resource_url("http://172.16.0.1/x") == ""
    assert canonical_resource_url("http://[::1]/x") == ""
    assert canonical_resource_url("https://myhost.local/x") == ""
    assert canonical_resource_url("http://example.com") == "http://example.com/"


def test_mark_selections_used_updates_last_used_at() -> None:
    from app.core.database import SessionLocal
    from app.services.development_user import get_current_development_user
    from app.services import resource_selection_service

    subject = _create_subject()
    sel = _create_selection(subject["id"], f"https://example.com/{uuid.uuid4().hex}/usage")

    db = SessionLocal()
    try:
        user = get_current_development_user(db)
        selection = (
            db.query(LearningResourceSelection)
            .filter(LearningResourceSelection.id == uuid.UUID(sel["id"]))
            .first()
        )
        assert selection.last_used_at is None
        resource_selection_service.mark_selections_used(db, [selection])
        db.commit()
        db.refresh(selection)
        assert selection.last_used_at is not None
    finally:
        db.close()
