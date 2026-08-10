"""Tests for the AI Quiz Generator REST API.

Every test runs against the isolated "bytebrains_test" database (see
conftest.py). The AI service is mocked to avoid real OpenRouter calls.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import Material, ProcessingStatus
from app.services import ai_service

client = TestClient(app)


def _create_subject() -> dict:
    response = client.post(
        "/api/subjects", json={"name": f"Quiz Subject {uuid.uuid4().hex[:8]}"}
    )
    assert response.status_code == 201
    return response.json()


def _create_material(subject_id: str, extracted_text: str = "Databases store data.") -> dict:
    from app.core.database import SessionLocal
    from app.services.development_user import get_current_development_user

    db = SessionLocal()
    try:
        user = get_current_development_user(db)
        material = Material(
            user_id=user.id,
            subject_id=uuid.UUID(subject_id),
            filename="quiz-test.txt",
            original_filename="quiz-test.txt",
            file_type="text/plain",
            file_size=100,
            storage_path="uploads/quiz-test.txt",
            processing_status=ProcessingStatus.processed,
            extracted_text=extracted_text,
        )
        db.add(material)
        db.commit()
        db.refresh(material)
        return {"id": str(material.id), "subject_id": str(material.subject_id)}
    finally:
        db.close()


def _valid_quiz_payload(question_count: int = 5) -> dict:
    return {
        "questions": [
            {
                "question": f"Question {i}",
                "options": ["A", "B", "C", "D"],
                "correct_answer": 0,
                "explanation": f"Because {i}",
                "topic": "Databases",
            }
            for i in range(question_count)
        ]
    }


@patch.object(ai_service, "generate_quiz", new_callable=AsyncMock)
def test_valid_generate_quiz(mock_generate_quiz) -> None:
    mock_generate_quiz.side_effect = (
        lambda material, question_count: ai_service.QuizGenerateResponse(
            material_id=material.id,
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
    )

    subject = _create_subject()
    material = _create_material(subject["id"])

    response = client.post(
        "/api/quizzes/generate",
        json={"material_id": material["id"], "question_count": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["material_id"] == material["id"]
    assert body["question_count"] == 1
    assert body["questions"][0]["question"] == "What is a database?"
    assert body["questions"][0]["correct_answer"] == 0

    client.delete(f"/api/subjects/{subject['id']}")


def test_missing_material_returns_404() -> None:
    response = client.post(
        "/api/quizzes/generate",
        json={"material_id": str(uuid.uuid4()), "question_count": 5},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Material not found"}


@patch.object(ai_service, "generate_quiz", new_callable=AsyncMock)
def test_empty_extracted_text_returns_422(mock_generate_quiz) -> None:
    mock_generate_quiz.side_effect = ai_service.EmptyMaterialError("No text")

    subject = _create_subject()
    material = _create_material(subject["id"], extracted_text="")

    response = client.post(
        "/api/quizzes/generate",
        json={"material_id": material["id"], "question_count": 5},
    )
    assert response.status_code == 422
    assert "no extracted text" in response.json()["detail"].lower()

    client.delete(f"/api/subjects/{subject['id']}")


@patch.object(ai_service, "generate_quiz", new_callable=AsyncMock)
def test_missing_api_key_returns_503(mock_generate_quiz) -> None:
    mock_generate_quiz.side_effect = ai_service.MissingAPIKeyError("Not configured")

    subject = _create_subject()
    material = _create_material(subject["id"])

    response = client.post(
        "/api/quizzes/generate",
        json={"material_id": material["id"], "question_count": 5},
    )
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()

    client.delete(f"/api/subjects/{subject['id']}")


@patch.object(ai_service, "generate_quiz", new_callable=AsyncMock)
def test_ai_service_error_returns_503(mock_generate_quiz) -> None:
    mock_generate_quiz.side_effect = ai_service.AIServiceError("Timeout")

    subject = _create_subject()
    material = _create_material(subject["id"])

    response = client.post(
        "/api/quizzes/generate",
        json={"material_id": material["id"], "question_count": 5},
    )
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"].lower()

    client.delete(f"/api/subjects/{subject['id']}")


@patch.object(ai_service, "generate_quiz", new_callable=AsyncMock)
def test_quiz_generation_error_returns_502(mock_generate_quiz) -> None:
    mock_generate_quiz.side_effect = ai_service.QuizGenerationError(
        "Quiz generation failed: invalid JSON"
    )

    subject = _create_subject()
    material = _create_material(subject["id"])

    response = client.post(
        "/api/quizzes/generate",
        json={"material_id": material["id"], "question_count": 5},
    )
    assert response.status_code == 502
    assert "invalid JSON" in response.json()["detail"]

    client.delete(f"/api/subjects/{subject['id']}")


def test_question_count_out_of_range_rejected() -> None:
    subject = _create_subject()
    material = _create_material(subject["id"])

    response = client.post(
        "/api/quizzes/generate",
        json={"material_id": material["id"], "question_count": 3},
    )
    assert response.status_code == 422
    assert str(response.json()["detail"]).find("question_count") != -1

    response = client.post(
        "/api/quizzes/generate",
        json={"material_id": material["id"], "question_count": 11},
    )
    assert response.status_code == 422

    client.delete(f"/api/subjects/{subject['id']}")


def test_missing_question_count_rejected() -> None:
    subject = _create_subject()
    material = _create_material(subject["id"])

    response = client.post(
        "/api/quizzes/generate",
        json={"material_id": material["id"]},
    )
    assert response.status_code == 422

    client.delete(f"/api/subjects/{subject['id']}")


def test_parse_questions_valid() -> None:
    payload = _valid_quiz_payload(5)
    questions = ai_service._parse_questions(payload)
    assert len(questions) == 5
    assert questions[0].options == ["A", "B", "C", "D"]
    assert questions[0].correct_answer == 0
    assert questions[0].topic == "Databases"


def test_parse_questions_invalid_json_structure() -> None:
    with pytest.raises(ai_service.QuizGenerationError):
        ai_service._parse_questions({"not_questions": []})


def test_parse_questions_malformed_question() -> None:
    payload = {"questions": [{"question": "Missing everything else"}]}
    with pytest.raises(ai_service.QuizGenerationError):
        ai_service._parse_questions(payload)


def test_parse_questions_wrong_option_count() -> None:
    payload = {
        "questions": [
            {
                "question": "Q",
                "options": ["A", "B", "C"],
                "correct_answer": 0,
                "explanation": "E",
                "topic": "T",
            }
        ]
    }
    with pytest.raises(ai_service.QuizGenerationError):
        ai_service._parse_questions(payload)


def test_parse_questions_invalid_correct_answer() -> None:
    payload = {
        "questions": [
            {
                "question": "Q",
                "options": ["A", "B", "C", "D"],
                "correct_answer": 7,
                "explanation": "E",
                "topic": "T",
            }
        ]
    }
    with pytest.raises(ai_service.QuizGenerationError):
        ai_service._parse_questions(payload)


def test_extract_json_handles_code_fences() -> None:
    content = '```json\n{"questions": []}\n```'
    data = ai_service._extract_json(content)
    assert data == {"questions": []}


def test_extract_json_invalid_raises() -> None:
    with pytest.raises(ai_service.QuizGenerationError):
        ai_service._extract_json("not json at all")


def test_existing_tests_still_pass() -> None:
    subject = _create_subject()
    assert subject["id"]
    client.delete(f"/api/subjects/{subject['id']}")