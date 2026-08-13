"""Tests for web-resource-driven AI modes (Phase 12).

Coverage:
- Tutor: web selections present -> ask_tutor_with_learning_context used;
  no material and no web -> instructive 200; empty-material + web -> context path
- Quiz: web selections present -> generate_quiz_from_context used and
  subject_id set on response; subject without sources -> 422;
  QuizGenerationError in context mode -> 502
- Study Plan: web selections included as web_resource_context and marked used
- Validation: neither material_id nor subject_id -> 422 for tutor and quiz
"""

import uuid
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import Material, ProcessingStatus
from app.services import ai_service

client = TestClient(app)


def _create_subject() -> dict:
    response = client.post(
        "/api/subjects", json={"name": f"Web Mode Subject {uuid.uuid4().hex[:8]}"}
    )
    assert response.status_code == 201
    return response.json()


def _create_material(subject_id: str, extracted_text: str = "Web content about databases.") -> dict:
    from app.core.database import SessionLocal
    from app.services.development_user import get_current_development_user

    db = SessionLocal()
    try:
        user = get_current_development_user(db)
        material = Material(
            user_id=user.id,
            subject_id=uuid.UUID(subject_id),
            filename="web-test.txt",
            original_filename="web-test.txt",
            file_type="text/plain",
            file_size=100,
            storage_path="uploads/web-test.txt",
            processing_status=ProcessingStatus.processed,
            extracted_text=extracted_text,
        )
        db.add(material)
        db.commit()
        db.refresh(material)
        return {"id": str(material.id), "subject_id": str(material.subject_id)}
    finally:
        db.close()


def _create_selection(subject_id: str, url: str | None = None) -> dict:
    if url is None:
        url = f"https://docs.example.com/{uuid.uuid4().hex}/guide"
    response = client.post(
        "/api/learning-resources/select",
        json={"subject_id": subject_id, "title": "Official Guide", "url": url},
    )
    assert response.status_code == 201
    return response.json()


def _fake_quiz_response(material_id=None, subject_id=None):
    return ai_service.QuizGenerateResponse(
        material_id=material_id,
        subject_id=subject_id,
        questions=[
            ai_service.QuizQuestion(
                question="What is a database?",
                options=["A", "B", "C", "D"],
                correct_answer=0,
                explanation="A database stores data.",
                topic="Databases",
            )
        ],
        question_count=1,
    )


# ---------------------------------------------------------------------------
# Tutor
# ---------------------------------------------------------------------------


@patch.object(ai_service, "ask_tutor_with_learning_context", new_callable=AsyncMock)
def test_tutor_web_mode_uses_context_function(mock_context_tutor) -> None:
    mock_context_tutor.return_value = "Web-grounded answer."
    subject = _create_subject()
    _create_selection(subject["id"])

    response = client.post(
        "/api/tutor/ask",
        json={"subject_id": subject["id"], "question": "What is X?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Web-grounded answer."
    assert body["material_id"] is None
    mock_context_tutor.assert_awaited_once()
    args, kwargs = mock_context_tutor.await_args
    assert "Web Official Guide" in args[1] or "docs.example.com" in args[1]


@patch.object(ai_service, "ask_tutor_with_learning_context", new_callable=AsyncMock)
@patch.object(ai_service, "ask_tutor", new_callable=AsyncMock)
def test_tutor_material_with_web_uses_context_function(mock_ask_tutor, mock_context_tutor) -> None:
    mock_context_tutor.return_value = "Combined answer."
    subject = _create_subject()
    material = _create_material(subject["id"])
    _create_selection(subject["id"])

    response = client.post(
        "/api/tutor/ask",
        json={"material_id": material["id"], "question": "Explain?"},
    )
    assert response.status_code == 200
    assert response.json()["answer"] == "Combined answer."
    mock_ask_tutor.assert_not_awaited()
    mock_context_tutor.assert_awaited_once()


@patch.object(ai_service, "ask_tutor", new_callable=AsyncMock)
def test_tutor_without_any_content_returns_instructive_200(mock_ask_tutor) -> None:
    subject = _create_subject()

    response = client.post(
        "/api/tutor/ask",
        json={"subject_id": subject["id"], "question": "What is X?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "find learning resources" in body["answer"].lower()
    mock_ask_tutor.assert_not_awaited()


@patch.object(ai_service, "ask_tutor_with_learning_context", new_callable=AsyncMock)
def test_tutor_empty_material_with_web_uses_context_function(mock_context_tutor) -> None:
    mock_context_tutor.return_value = "Web-only answer."
    subject = _create_subject()
    material = _create_material(subject["id"], extracted_text="")
    _create_selection(subject["id"])

    response = client.post(
        "/api/tutor/ask",
        json={"material_id": material["id"], "question": "Explain?"},
    )
    assert response.status_code == 200
    assert response.json()["answer"] == "Web-only answer."
    mock_context_tutor.assert_awaited_once()


def test_tutor_requires_source() -> None:
    response = client.post("/api/tutor/ask", json={"question": "Hi"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------


@patch.object(ai_service, "generate_quiz_from_context", new_callable=AsyncMock)
def test_quiz_web_mode_uses_context_function(mock_context_quiz) -> None:
    mock_context_quiz.return_value = _fake_quiz_response()
    subject = _create_subject()
    _create_selection(subject["id"])

    response = client.post(
        "/api/quizzes/generate",
        json={"subject_id": subject["id"], "question_count": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["subject_id"] == subject["id"]
    assert body["material_id"] is None
    assert body["question_count"] == 1
    mock_context_quiz.assert_awaited_once()
    args, kwargs = mock_context_quiz.await_args
    assert kwargs["material_id"] is None


@patch.object(ai_service, "generate_quiz_from_context", new_callable=AsyncMock)
def test_quiz_material_with_web_uses_context_function(mock_context_quiz) -> None:
    mock_context_quiz.return_value = _fake_quiz_response()
    subject = _create_subject()
    material = _create_material(subject["id"])
    _create_selection(subject["id"])

    response = client.post(
        "/api/quizzes/generate",
        json={"material_id": material["id"], "question_count": 5},
    )
    assert response.status_code == 200
    assert response.json()["subject_id"] == subject["id"]
    mock_context_quiz.assert_awaited_once()
    args, kwargs = mock_context_quiz.await_args
    assert kwargs["material_id"] == uuid.UUID(material["id"])


def test_quiz_subject_without_sources_returns_422() -> None:
    subject = _create_subject()
    response = client.post(
        "/api/quizzes/generate",
        json={"subject_id": subject["id"], "question_count": 5},
    )
    assert response.status_code == 422
    assert "no learning context" in response.json()["detail"].lower()


@patch.object(ai_service, "generate_quiz_from_context", new_callable=AsyncMock)
def test_quiz_web_mode_generation_error_returns_502(mock_context_quiz) -> None:
    mock_context_quiz.side_effect = ai_service.QuizGenerationError("invalid JSON")
    subject = _create_subject()
    _create_selection(subject["id"])

    response = client.post(
        "/api/quizzes/generate",
        json={"subject_id": subject["id"], "question_count": 5},
    )
    assert response.status_code == 502


@patch.object(ai_service, "generate_quiz_from_context", new_callable=AsyncMock)
def test_quiz_web_mode_missing_key_returns_503(mock_context_quiz) -> None:
    mock_context_quiz.side_effect = ai_service.MissingAPIKeyError("nope")
    subject = _create_subject()
    _create_selection(subject["id"])

    response = client.post(
        "/api/quizzes/generate",
        json={"subject_id": subject["id"], "question_count": 5},
    )
    assert response.status_code == 503


def test_quiz_requires_source() -> None:
    response = client.post(
        "/api/quizzes/generate", json={"question_count": 5}
    )
    assert response.status_code == 422


def test_submit_attempt_subject_only_creates_attempt() -> None:
    from app.core.database import SessionLocal
    from app.models import QuizAttempt

    subject = _create_subject()

    try:
        response = client.post(
            "/api/quizzes/submit",
            json={
                "subject_id": subject["id"],
                "total_questions": 5,
                "correct_answers": 4,
                "topic_results": [{"topic": "Databases", "correct": 4, "total": 5}],
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["score"] == 80
        assert "web resources" in body["quiz_title"]

        attempts = client.get("/api/quizzes/attempts").json()
        assert attempts[0]["subject_name"] == subject["name"]
    finally:
        db = SessionLocal()
        try:
            db.query(QuizAttempt).filter(
                QuizAttempt.subject_id == uuid.UUID(subject["id"])
            ).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()
        client.delete(f"/api/subjects/{subject['id']}")


def test_submit_attempt_requires_source() -> None:
    response = client.post(
        "/api/quizzes/submit",
        json={"total_questions": 5, "correct_answers": 4},
    )
    assert response.status_code == 422


def test_submit_attempt_missing_subject_returns_404() -> None:
    response = client.post(
        "/api/quizzes/submit",
        json={
            "subject_id": str(uuid.uuid4()),
            "total_questions": 5,
            "correct_answers": 4,
        },
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Subject not found"}


# ---------------------------------------------------------------------------
# Study Plan
# ---------------------------------------------------------------------------


def _plan_payload(subject_id: str) -> dict:
    return {
        "subject_id": subject_id,
        "days_available": 3,
        "hours_per_day": 2,
        "focus": "Balanced",
        "exam_date": None,
        "weak_topics": [],
    }


@patch.object(ai_service, "generate_study_plan", new_callable=AsyncMock)
def test_study_plan_web_mode_includes_web_context(mock_plan) -> None:
    from app.models import LearningResourceSelection

    mock_plan.side_effect = (
        lambda **kwargs: ai_service.StudyPlanGenerateResponse(
            subject_id=kwargs["subject_id"],
            days=[
                ai_service.StudyPlanDay(
                    day=1,
                    tasks=[
                        ai_service.StudyPlanTask(
                            title="Read guide",
                            duration_minutes=45,
                            type=ai_service.PlanTaskType.study,
                        )
                    ],
                )
            ],
        )
    )
    subject = _create_subject()
    selection = _create_selection(subject["id"], f"https://docs.example.com/{uuid.uuid4().hex}/guide")

    response = client.post("/api/study-plan/generate", json=_plan_payload(subject["id"]))
    assert response.status_code == 200
    args, kwargs = mock_plan.await_args
    assert "docs.example.com" in kwargs["web_resource_context"]

    from app.core.database import SessionLocal
    from app.services.development_user import get_current_development_user

    db = SessionLocal()
    try:
        user = get_current_development_user(db)
        stored = (
            db.query(LearningResourceSelection)
            .filter(LearningResourceSelection.id == uuid.UUID(selection["id"]))
            .first()
        )
        assert stored is not None
        assert stored.last_used_at is not None
    finally:
        db.close()


@patch.object(ai_service, "generate_study_plan", new_callable=AsyncMock)
def test_study_plan_without_web_passes_empty_context(mock_plan) -> None:
    mock_plan.side_effect = (
        lambda **kwargs: ai_service.StudyPlanGenerateResponse(
            subject_id=kwargs["subject_id"],
            days=[
                ai_service.StudyPlanDay(
                    day=1,
                    tasks=[
                        ai_service.StudyPlanTask(
                            title="Study",
                            duration_minutes=45,
                            type=ai_service.PlanTaskType.study,
                        )
                    ],
                )
            ],
        )
    )
    subject = _create_subject()

    response = client.post("/api/study-plan/generate", json=_plan_payload(subject["id"]))
    assert response.status_code == 200
    args, kwargs = mock_plan.await_args
    assert kwargs["web_resource_context"] == ""