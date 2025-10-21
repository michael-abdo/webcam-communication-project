import os
import io
import json
from datetime import datetime, timezone

import pytest

# Configure database before importing application modules
TEST_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test_capture_api.db"))
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["CAPTURE_API_TOKEN"] = "test-token"

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


def auth_headers():
    return {"Authorization": "Bearer test-token"}


def test_create_session_validation(client):
    response = client.post("/api/sessions", json={}, headers=auth_headers())
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
        headers=auth_headers(),
    )

    assert session_resp.status_code == 201
    session_body = session_resp.get_json()
    session_id = session_body["id"]

    participant_resp = client.post(
        f"/api/sessions/{session_id}/participants",
        json={"device_id": "cam-001", "status": "ready"},
        headers=auth_headers(),
    )
    assert participant_resp.status_code == 201
    participant_body = participant_resp.get_json()

    metadata = {
        "sequence_no": 0,
        "checksum": "abc123",
        "duration_ms": 5000,
        "participant_id": participant_body["id"],
        "mime_type": "video/webm;codecs=vp8,opus",
        "file_extension": "webm",
    }
    chunk_resp = client.post(
        f"/api/sessions/{session_id}/chunks",
        data={
            "metadata": json.dumps(metadata),
            "media": (io.BytesIO(b"fake-chunk"), "chunk0000.webm", "video/webm"),
        },
        headers=auth_headers(),
        content_type="multipart/form-data",
    )
    assert chunk_resp.status_code == 202

    session_detail = client.get(f"/api/sessions/{session_id}", headers=auth_headers())
    assert session_detail.status_code == 200
    detail_body = session_detail.get_json()
    assert detail_body["id"] == session_id
    assert len(detail_body["participants"]) == 1
    assert len(detail_body["chunks"]) == 1


def test_session_list_endpoint(client):
    consent_at = datetime.now(timezone.utc).isoformat()
    client.post(
        "/api/sessions",
        json={
            "facilitator_id": "fac-list",
            "consent_at": consent_at,
            "device_kind": "macbook-pro",
        },
        headers=auth_headers(),
    )

    response = client.get("/api/sessions", headers=auth_headers())
    assert response.status_code == 200
    payload = response.get_json()
    assert "sessions" in payload
    assert payload["count"] == len(payload["sessions"])
    assert any(session["facilitator_id"] == "fac-list" for session in payload["sessions"])


def test_chunk_conflict(client):
    consent_at = datetime.now(timezone.utc).isoformat()
    session_resp = client.post(
        "/api/sessions",
        json={
            "facilitator_id": "fac-321",
            "consent_at": consent_at,
            "device_kind": "macbook-pro",
        },
        headers=auth_headers(),
    )
    session_id = session_resp.get_json()["id"]

    first_meta = {
        "sequence_no": 1,
        "checksum": "abc",
        "duration_ms": 5000,
        "mime_type": "video/webm",
        "file_extension": "webm",
    }
    first = client.post(
        f"/api/sessions/{session_id}/chunks",
        data={
            "metadata": json.dumps(first_meta),
            "media": (io.BytesIO(b"chunk-a"), "chunk0001.webm", "video/webm"),
        },
        headers=auth_headers(),
        content_type="multipart/form-data",
    )
    assert first.status_code == 202

    dup_meta = {
        "sequence_no": 1,
        "checksum": "def",
        "duration_ms": 5000,
        "mime_type": "video/webm",
        "file_extension": "webm",
    }
    second = client.post(
        f"/api/sessions/{session_id}/chunks",
        data={
            "metadata": json.dumps(dup_meta),
            "media": (io.BytesIO(b"chunk-b"), "chunk0001b.webm", "video/webm"),
        },
        headers=auth_headers(),
        content_type="multipart/form-data",
    )
    assert second.status_code == 409


def test_missing_token_rejected(client):
    response = client.post(
        "/api/sessions",
        json={
            "facilitator_id": "fac-unauth",
            "consent_at": datetime.now(timezone.utc).isoformat(),
            "device_kind": "macbook-pro",
        },
    )
    assert response.status_code == 401
