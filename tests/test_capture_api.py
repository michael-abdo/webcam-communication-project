import os
import io
import json
from datetime import datetime, timezone

import pytest

import streaming.s3_handler as s3_handler
import blueprints.capture_api as capture_api_module

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




@pytest.fixture(autouse=True)
def metrics_stub(monkeypatch):
    class Stub:
        def __init__(self):
            self.incr_calls = []
            self.timing_calls = []

        def incr(self, name, count=1, rate=1.0):
            self.incr_calls.append((name, count, rate))

        def timing(self, name, value, rate=1.0):
            self.timing_calls.append((name, value, rate))

    stub = Stub()
    monkeypatch.setattr(capture_api_module, "metrics", lambda: stub)
    yield stub


@pytest.fixture(autouse=True)
def stub_s3_client(monkeypatch):
    class StubClient:
        def upload_fileobj(self, file_obj, bucket, key, ExtraArgs=None):
            file_obj.seek(0, 2)  # drain file

        def generate_presigned_url(self, operation_name, Params=None, ExpiresIn=3600):
            return f"https://example.com/{Params['Key']}"

        def head_bucket(self, Bucket):
            return True

    stub = StubClient()
    monkeypatch.setattr(s3_handler, "get_s3_client", lambda: stub)
    monkeypatch.setattr(s3_handler, "generate_download_url", lambda key, expiration=3600: f"https://example.com/{key}")
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


def test_session_lifecycle(client, metrics_stub):
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

    assert any(name == "phase1.chunk.uploaded" for name, _, _ in metrics_stub.incr_calls)
    assert any(name == "phase1.chunk.upload_latency_ms" for name, _, _ in metrics_stub.timing_calls)

    transcript_resp = client.post(
        f"/api/sessions/{session_id}/transcript",
        json={
            "status": "completed",
            "storage_key": "transcripts/test.txt",
            "mime_type": "text/plain",
            "generated_at": consent_at,
            "source": "unit-test",
        },
        headers=auth_headers(),
    )
    assert transcript_resp.status_code == 200
    assert any(name == "phase1.transcript.updated" for name, _, _ in metrics_stub.incr_calls)

    log_resp = client.post(
        f"/api/sessions/{session_id}/logs",
        json={
            "status": "completed",
            "log_type": "ingest",
            "storage_key": "logs/test.log",
            "message": "ingest finished",
            "recorded_at": consent_at,
        },
        headers=auth_headers(),
    )
    assert log_resp.status_code == 201
    assert any(name == "phase1.log.updated" for name, _, _ in metrics_stub.incr_calls)

    detail_body = client.get(f"/api/sessions/{session_id}", headers=auth_headers()).get_json()
    assert detail_body["id"] == session_id
    assert len(detail_body["participants"]) == 1
    assert len(detail_body["chunks"]) == 1
    assert detail_body["transcript_status"] == "completed"
    assert detail_body["log_status"] == "completed"
    assert detail_body["transcript"]["download_url"].startswith("https://example.com/")
    assert detail_body["logs"][0]["download_url"].startswith("https://example.com/")
    assert detail_body["chunks"][0]["download_url"].startswith("https://example.com/")

    download_resp = client.get(
        f"/api/sessions/{session_id}/chunks/0/download",
        headers=auth_headers(),
    )
    assert download_resp.status_code == 200
    assert download_resp.get_json()["url"].startswith("https://example.com/")
    assert any(name == "phase1.chunk.download_requested" for name, _, _ in metrics_stub.incr_calls)

    transcript_download = client.get(
        f"/api/sessions/{session_id}/transcript/download",
        headers=auth_headers(),
    )
    assert transcript_download.status_code == 200
    assert transcript_download.get_json()["url"].startswith("https://example.com/")
    assert any(name == "phase1.transcript.download_requested" for name, _, _ in metrics_stub.incr_calls)

    log_id = detail_body["logs"][0]["id"]
    log_download = client.get(
        f"/api/sessions/{session_id}/logs/{log_id}/download",
        headers=auth_headers(),
    )
    assert log_download.status_code == 200
    assert log_download.get_json()["url"].startswith("https://example.com/")
    assert any(name == "phase1.log.download_requested" for name, _, _ in metrics_stub.incr_calls)


def test_session_list_endpoint(client, metrics_stub):
    consent_at = datetime.now(timezone.utc).isoformat()
    session_resp = client.post(
        "/api/sessions",
        json={
            "facilitator_id": "fac-list",
            "consent_at": consent_at,
            "device_kind": "macbook-pro",
        },
        headers=auth_headers(),
    )
    session_id = session_resp.get_json()["id"]

    client.post(
        f"/api/sessions/{session_id}/chunks",
        data={
            "metadata": json.dumps({
                "sequence_no": 0,
                "checksum": "xyz",
                "duration_ms": 4000,
                "mime_type": "video/webm",
                "file_extension": "webm",
            }),
            "media": (io.BytesIO(b"temp"), "chunk0000.webm", "video/webm"),
        },
        headers=auth_headers(),
        content_type="multipart/form-data",
    )

    client.post(
        f"/api/sessions/{session_id}/transcript",
        json={"status": "completed", "storage_key": "transcripts/list.txt"},
        headers=auth_headers(),
    )

    client.post(
        f"/api/sessions/{session_id}/logs",
        json={"status": "completed", "storage_key": "logs/list.log"},
        headers=auth_headers(),
    )

    response = client.get("/api/sessions", headers=auth_headers())
    assert response.status_code == 200
    payload = response.get_json()
    assert "sessions" in payload
    assert payload["count"] == len(payload["sessions"])
    session = next(item for item in payload["sessions"] if item["facilitator_id"] == "fac-list")
    assert session["transcript_status"] == "completed"
    assert session["log_status"] == "completed"
    assert session["chunk_count"] == 1


def test_chunk_conflict(client, metrics_stub):
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
    assert any(name == "phase1.chunk.conflict" for name, _, _ in metrics_stub.incr_calls)


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
