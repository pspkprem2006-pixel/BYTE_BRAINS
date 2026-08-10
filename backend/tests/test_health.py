"""Health endpoint tests using the FastAPI TestClient."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_expected_json() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ByteBrains API"}


def test_health_db_responds() -> None:
    # Reports "connected" when PostgreSQL is up (local dev), otherwise 503.
    response = client.get("/health/db")
    assert response.status_code in (200, 503)