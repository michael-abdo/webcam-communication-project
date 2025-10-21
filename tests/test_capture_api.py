import os
from datetime import datetime, timezone

import pytest

# Configure database before importing application modules
TEST_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test_capture_api.db"))
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

from app_lightweight import app  # noqa: E402
from models import init_engine  # noqa: E402
from models.database import Base, engine  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    init_engine()
    return app.test_client()


def test_create_session_validation(client):
    response = client.post("/api/sessions", json={})
    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "missing_fields"


def test_session_lifecycle(client):
    consent_at = datetime.now(timezone.utc).isoformat()
    session_resp = client.post(
        "/api/sessions",
        json={
            "facilitator_id": "fac-123",
            "consent_at": consent_at,
            "device_kind": "macbook-pro",
            "locale": "en-US",
        },
    )

    assert session_resp.status_code == 201
    session_body = session_resp.get_json()
    session_id = session_body["id"]

    participant_resp = client.post(
        f"/api/sessions/{session_id}/participants",
        json={"device_id": "cam-001", "status": "ready"},
    )
    assert participant_resp.status_code == 201
    participant_body = participant_resp.get_json()

    chunk_resp = client.post(
        f"/api/sessions/{session_id}/chunks",
        json={
            "sequence_no": 0,
            "checksum": "abc123",
            "duration_ms": 5000,
            "storage_key": "recordings/test/chunk_0000.webm",
            "participant_id": participant_body["id"],
        },
    )
    assert chunk_resp.status_code == 202

    session_detail = client.get(f"/api/sessions/{session_id}")
    assert session_detail.status_code == 200
    detail_body = session_detail.get_json()
    assert detail_body["id"] == session_id
    assert len(detail_body["participants"]) == 1
    assert len(detail_body["chunks"]) == 1


def test_chunk_conflict(client):
    consent_at = datetime.now(timezone.utc).isoformat()
    session_resp = client.post(
        "/api/sessions",
        json={
            "facilitator_id": "fac-321",
            "consent_at": consent_at,
            "device_kind": "macbook-pro",
        },
    )
    session_id = session_resp.get_json()["id"]

    first = client.post(
        f"/api/sessions/{session_id}/chunks",
        json={
            "sequence_no": 1,
            "checksum": "abc",
            "duration_ms": 5000,
            "storage_key": "recordings/test/chunk_0001.webm",
        },
    )
    assert first.status_code == 202

    second = client.post(
        f"/api/sessions/{session_id}/chunks",
        json={
            "sequence_no": 1,
            "checksum": "def",
            "duration_ms": 5000,
            "storage_key": "recordings/test/chunk_0001_dup.webm",
        },
    )
    assert second.status_code == 409
