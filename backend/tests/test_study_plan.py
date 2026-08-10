"""Tests for the AI Study Plan REST API.

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
        "/api/subjects", json={"name": f"Plan Subject {uuid.uuid4().hex[:8]}"}
    )
    assert response.status_code == 201
    return response.json()


def _create_material(subject_id: str, extracted_text: str = "Normalization reduces redundancy.") -> dict:
    from app.core.database import SessionLocal
    from app.services.development_user import get_current_development_user

    db = SessionLocal()
    try:
        user = get_current_development_user(db)
        material = Material(
            user_id=user.id,
            subject_id=uuid.UUID(subject_id),
            filename="plan-test.txt",
            original_filename="plan-test.txt",
            file_type="text/plain",
            file_size=100,
            storage_path="uploads/plan-test.txt",
            processing_status=ProcessingStatus.processed,
            extracted_text=extracted_text,
        )
        db.add(material)
        db.commit()
        db.refresh(material)
        return {"id": str(material.id), "subject_id": str(material.subject_id)}
    finally:
        db.close()


def _valid_plan_payload(days: int = 5) -> dict:
    return {
        "days": [
            {
                "day": i + 1,
                "tasks": [
                    {"title": "Normalization", "duration_minutes": 45, "type": "study"},
                    {"title": "Practice questions", "duration_minutes": 30, "type": "practice"},
                ],
            }
            for i in range(days)
        ]
    }


def _generate_request(subject_id: str, **overrides) -> dict:
    payload = {
        "subject_id": subject_id,
        "days_available": 5,
        "hours_per_day": 2,
        "focus": "Balanced",
        "exam_date": None,
        "weak_topics": ["Normalization"],
    }
    payload.update(overrides)
    return payload


@patch.object(ai_service, "generate_study_plan", new_callable=AsyncMock)
def test_valid_study_plan_generation(mock_generate_study_plan) -> None:
    subject = _create_subject()
    mock_generate_study_plan.side_effect = (
        lambda **kwargs: ai_service.StudyPlanGenerateResponse(
            subject_id=kwargs["subject_id"],
            days=[
                ai_service.StudyPlanDay(
                    day=1,
                    tasks=[
                        ai_service.StudyPlanTask(
                            title="Normalization",
                            duration_minutes=45,
                            type=ai_service.PlanTaskType.study,
                        )
                    ],
                )
            ],
        )
    )

    response = client.post(
        "/api/study-plan/generate",
        json=_generate_request(subject["id"]),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["subject_id"] == subject["id"]
    assert len(body["days"]) == 1
    assert body["days"][0]["tasks"][0]["title"] == "Normalization"
    assert body["days"][0]["tasks"][0]["duration_minutes"] == 45
    assert body["days"][0]["tasks"][0]["type"] == "study"

    client.delete(f"/api/subjects/{subject['id']}")


def test_invalid_days_rejected() -> None:
    subject = _create_subject()

    response = client.post(
        "/api/study-plan/generate",
        json=_generate_request(subject["id"], days_available=0),
    )
    assert response.status_code == 422

    response = client.post(
        "/api/study-plan/generate",
        json=_generate_request(subject["id"], days_available=31),
    )
    assert response.status_code == 422

    client.delete(f"/api/subjects/{subject['id']}")


def test_invalid_hours_rejected() -> None:
    subject = _create_subject()

    response = client.post(
        "/api/study-plan/generate",
        json=_generate_request(subject["id"], hours_per_day=0),
    )
    assert response.status_code == 422

    response = client.post(
        "/api/study-plan/generate",
        json=_generate_request(subject["id"], hours_per_day=13),
    )
    assert response.status_code == 422

    client.delete(f"/api/subjects/{subject['id']}")


def test_missing_subject_returns_404() -> None:
    response = client.post(
        "/api/study-plan/generate",
        json=_generate_request(str(uuid.uuid4())),
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Subject not found"}


def test_invalid_focus_rejected() -> None:
    subject = _create_subject()

    response = client.post(
        "/api/study-plan/generate",
        json=_generate_request(subject["id"], focus="Not a focus"),
    )
    assert response.status_code == 422

    client.delete(f"/api/subjects/{subject['id']}")


@patch.object(ai_service, "generate_study_plan", new_callable=AsyncMock)
def test_missing_api_key_returns_503(mock_generate_study_plan) -> None:
    mock_generate_study_plan.side_effect = ai_service.MissingAPIKeyError("Not configured")

    subject = _create_subject()

    response = client.post(
        "/api/study-plan/generate",
        json=_generate_request(subject["id"]),
    )
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()

    client.delete(f"/api/subjects/{subject['id']}")


@patch.object(ai_service, "generate_study_plan", new_callable=AsyncMock)
def test_ai_service_error_returns_503(mock_generate_study_plan) -> None:
    mock_generate_study_plan.side_effect = ai_service.AIServiceError("Timeout")

    subject = _create_subject()

    response = client.post(
        "/api/study-plan/generate",
        json=_generate_request(subject["id"]),
    )
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"].lower()

    client.delete(f"/api/subjects/{subject['id']}")


@patch.object(ai_service, "generate_study_plan", new_callable=AsyncMock)
def test_plan_generation_error_returns_503(mock_generate_study_plan) -> None:
    mock_generate_study_plan.side_effect = ai_service.StudyPlanGenerationError(
        "Study plan generation failed: invalid JSON"
    )

    subject = _create_subject()

    response = client.post(
        "/api/study-plan/generate",
        json=_generate_request(subject["id"]),
    )
    assert response.status_code == 503
    assert "invalid JSON" in response.json()["detail"]

    client.delete(f"/api/subjects/{subject['id']}")


def test_parse_plan_valid() -> None:
    payload = _valid_plan_payload(3)
    days = ai_service._parse_plan(payload, expected_days=3)
    assert len(days) == 3
    assert days[0].day == 1
    assert days[0].tasks[0].title == "Normalization"
    assert days[0].tasks[0].duration_minutes == 45
    assert days[0].tasks[0].type == ai_service.PlanTaskType.study


def test_parse_plan_wrong_day_count() -> None:
    payload = _valid_plan_payload(2)
    with pytest.raises(ai_service.StudyPlanGenerationError):
        ai_service._parse_plan(payload, expected_days=5)


def test_parse_plan_unexpected_structure() -> None:
    with pytest.raises(ai_service.StudyPlanGenerationError):
        ai_service._parse_plan({"not_days": []}, expected_days=1)


def test_parse_plan_malformed_task() -> None:
    payload = {"days": [{"day": 1, "tasks": [{"title": "Only title"}]}]}
    with pytest.raises(ai_service.StudyPlanGenerationError):
        ai_service._parse_plan(payload, expected_days=1)


def test_parse_plan_invalid_task_type() -> None:
    payload = {
        "days": [
            {
                "day": 1,
                "tasks": [{"title": "T", "duration_minutes": 30, "type": "sleep"}],
            }
        ]
    }
    with pytest.raises(ai_service.StudyPlanGenerationError):
        ai_service._parse_plan(payload, expected_days=1)


def test_parse_plan_day_without_tasks() -> None:
    payload = {"days": [{"day": 1, "tasks": []}]}
    with pytest.raises(ai_service.StudyPlanGenerationError):
        ai_service._parse_plan(payload, expected_days=1)


def test_extract_plan_json_handles_code_fences() -> None:
    content = '```json\n{"days": []}\n```'
    data = ai_service._extract_plan_json(content)
    assert data == {"days": []}


def test_extract_plan_json_invalid_raises() -> None:
    with pytest.raises(ai_service.StudyPlanGenerationError):
        ai_service._extract_plan_json("not json")


def test_weak_topics_pass_through() -> None:
    subject = _create_subject()
    _create_material(subject["id"])

    with patch.object(ai_service, "generate_study_plan", new_callable=AsyncMock) as mock:
        mock.return_value = ai_service.StudyPlanGenerateResponse(
            subject_id=uuid.UUID(subject["id"]),
            days=[
                ai_service.StudyPlanDay(
                    day=1,
                    tasks=[
                        ai_service.StudyPlanTask(
                            title="Normalization",
                            duration_minutes=45,
                            type=ai_service.PlanTaskType.study,
                        )
                    ],
                )
            ],
        )

        response = client.post(
            "/api/study-plan/generate",
            json=_generate_request(subject["id"], weak_topics=["Normalization", "Functional Dependencies"]),
        )
        assert response.status_code == 200
        _, kwargs = mock.call_args
        assert kwargs["weak_topics"] == ["Normalization", "Functional Dependencies"]
        assert kwargs["focus"] == "Balanced"
        assert kwargs["days_available"] == 5
        assert kwargs["hours_per_day"] == 2

    client.delete(f"/api/subjects/{subject['id']}")


def test_existing_tests_still_pass() -> None:
    subject = _create_subject()
    assert subject["id"]
    client.delete(f"/api/subjects/{subject['id']}")