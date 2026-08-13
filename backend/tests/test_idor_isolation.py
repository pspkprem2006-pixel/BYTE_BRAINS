"""Cross-user isolation (IDOR) audit tests.

Every endpoint is exercised with another user's resource IDs. All requests
act as the development user; a second user ("other@example.org") and their
data are created directly in the database. Every cross-user access must
fail with 404/422/409 — never return data.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal
from app.models import User, Subject, Material, LearningResourceSelection, QuizAttempt, UserProgress, Topic
from app.services.development_user import DEVELOPMENT_USER_EMAIL

client = TestClient(app)

OTHER_EMAIL = "other-audit@example.org"


@pytest.fixture(scope="module")
def other_user_data():
    db: Session = SessionLocal()
    other = (
        db.query(User).filter(User.email == OTHER_EMAIL).first()
        or User(name="Other User", email=OTHER_EMAIL)
    )
    if other.id is None:
        db.add(other)
        db.commit()
        db.refresh(other)
    suffix = uuid.uuid4().hex[:8]
    subject = Subject(owner_id=other.id, name=f"Audit Other Subject {suffix}")
    db.add(subject)
    db.commit()
    db.refresh(subject)
    material = Material(
        user_id=other.id,
        subject_id=subject.id,
        filename=f"other-{suffix}.txt",
        original_filename="other.txt",
        file_type="text/plain",
        file_size=10,
        processing_status="processed",
        extracted_text="Audit text about databases.",
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    selection = LearningResourceSelection(
        user_id=other.id,
        subject_id=subject.id,
        title="Other Resource",
        url=f"https://example.com/other/{suffix}",
        domain="example.com",
        resource_type="article",
        is_official=False,
        description="",
        source="web_search",
    )
    db.add(selection)
    db.commit()
    db.refresh(selection)
    topic = Topic(subject_id=subject.id, name="Audit Topic", order_index=0)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    attempt = QuizAttempt(
        user_id=other.id,
        subject_id=subject.id,
        quiz_title="Quiz: other",
        total_questions=2,
        correct_answers=1,
        score=50,
    )
    db.add(attempt)
    progress = UserProgress(
        user_id=other.id,
        topic_id=topic.id,
        mastery_score=70,
        topics_completed=1,
    )
    db.add(progress)
    db.commit()
    data = {
        "user_id": str(other.id),
        "subject_id": str(subject.id),
        "material_id": str(material.id),
        "selection_id": str(selection.id),
        "topic_id": str(topic.id),
    }
    db.close()
    yield data
    db = SessionLocal()
    db.query(UserProgress).filter(UserProgress.topic_id == topic.id).delete()
    db.query(QuizAttempt).filter(QuizAttempt.id == attempt.id).delete()
    db.query(Topic).filter(Topic.id == topic.id).delete()
    db.query(LearningResourceSelection).filter(LearningResourceSelection.id == selection.id).delete()
    db.query(Material).filter(Material.id == material.id).delete()
    db.query(Subject).filter(Subject.id == subject.id).delete()
    db.query(User).filter(User.id == other.id).delete()
    db.commit()
    db.close()


def _dev_user_id() -> str:
    db: Session = SessionLocal()
    user = db.query(User).filter(User.email == DEVELOPMENT_USER_EMAIL).first()
    uid = str(user.id)
    db.close()
    return uid


# --- 1. GET with another user's subject_id ----------------------------------


def test_other_subjects_not_listed(other_user_data):
    resp = client.get("/api/subjects")
    assert resp.status_code == 200
    ids = [s["id"] for s in resp.json()]
    assert other_user_data["subject_id"] not in ids


def test_tutor_ask_with_other_material(other_user_data):
    resp = client.post(
        "/api/tutor/ask",
        json={
            "material_id": other_user_data["material_id"],
            "question": "Explain indexes",
        },
    )
    assert resp.status_code == 404


def test_tutor_ask_with_other_subject(other_user_data):
    resp = client.post(
        "/api/tutor/ask",
        json={
            "subject_id": other_user_data["subject_id"],
            "question": "Explain indexes",
        },
    )
    assert resp.status_code == 404


def test_quiz_generate_with_other_material(other_user_data):
    with patch.object(
        __import__("app.services", fromlist=["ai_service"]).ai_service,
        "generate_quiz",
        new_callable=AsyncMock,
    ):
        resp = client.post(
            "/api/quizzes/generate",
            json={"material_id": other_user_data["material_id"], "question_count": 5},
        )
    assert resp.status_code == 404


def test_quiz_generate_with_other_subject(other_user_data):
    with patch.object(
        __import__("app.services", fromlist=["ai_service"]).ai_service,
        "generate_quiz_from_context",
        new_callable=AsyncMock,
    ):
        resp = client.post(
            "/api/quizzes/generate",
            json={"subject_id": other_user_data["subject_id"], "question_count": 5},
        )
    assert resp.status_code == 404


def test_quiz_submit_with_other_material(other_user_data):
    resp = client.post(
        "/api/quizzes/submit",
        json={
            "material_id": other_user_data["material_id"],
            "total_questions": 2,
            "correct_answers": 2,
            "topic_results": [{"topic": "Audit Topic", "correct": 2, "total": 2}],
        },
    )
    assert resp.status_code == 404


def test_quiz_submit_with_other_subject(other_user_data):
    resp = client.post(
        "/api/quizzes/submit",
        json={
            "subject_id": other_user_data["subject_id"],
            "total_questions": 2,
            "correct_answers": 1,
            "topic_results": [{"topic": "Audit Topic", "correct": 1, "total": 2}],
        },
    )
    assert resp.status_code == 404


def test_study_plan_for_other_subject(other_user_data):
    resp = client.post(
        "/api/study-plan/generate",
        json={
            "subject_id": other_user_data["subject_id"],
            "days_available": 7,
            "hours_per_day": 2,
            "focus": "Balanced",
        },
    )
    assert resp.status_code == 404


def test_delete_other_selection(other_user_data):
    resp = client.delete(
        f"/api/learning-resources/selected/{other_user_data['selection_id']}"
    )
    assert resp.status_code == 404


def test_other_selection_not_in_selected_list(other_user_data):
    resp = client.get("/api/learning-resources/selected")
    assert resp.status_code == 200
    ids = [s["id"] for s in resp.json()["resources"]]
    assert other_user_data["selection_id"] not in ids


def test_other_selection_not_in_subject_filter(other_user_data):
    resp = client.get(
        "/api/learning-resources/selected",
        params={"subject_id": other_user_data["subject_id"]},
    )
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_select_with_other_subject(other_user_data):
    resp = client.post(
        "/api/learning-resources/select",
        json={
            "subject_id": other_user_data["subject_id"],
            "title": "Sneaky",
            "url": f"https://example.com/sneaky/{uuid.uuid4().hex}",
        },
    )
    assert resp.status_code == 404


def test_materials_of_other_subject_not_listed(other_user_data):
    resp = client.get(
        "/api/materials", params={"subject_id": other_user_data["subject_id"]}
    )
    assert resp.status_code == 200
    ids = [m["id"] for m in resp.json()]
    assert other_user_data["material_id"] not in ids


def test_other_attempts_not_listed(other_user_data):
    resp = client.get("/api/quizzes/attempts")
    assert resp.status_code == 200
    items = resp.json()
    assert all(
        a.get("subject_id") != other_user_data["subject_id"] for a in items
    )


def test_other_progress_not_listed(other_user_data):
    resp = client.get("/api/progress")
    assert resp.status_code == 200
    items = resp.json()
    assert all(
        p.get("topic_id") != other_user_data["topic_id"] for p in items
    )


def test_delete_other_subject(other_user_data):
    resp = client.delete(f"/api/subjects/{other_user_data['subject_id']}")
    assert resp.status_code == 404


def test_dev_user_still_usable(other_user_data):
    resp = client.post(
        "/api/subjects",
        json={"name": f"Audit Dev Subject {uuid.uuid4().hex[:8]}"},
    )
    assert resp.status_code == 201
    sid = resp.json()["id"]
    client.delete(f"/api/subjects/{sid}")