"""API endpoints for Zoom RTMS ingestion service."""

from __future__ import annotations

from datetime import datetime, timezone
from http import HTTPStatus
import json
from typing import Any

from flask import Blueprint, jsonify, request, current_app

from config import get_capture_api_token
from models import SessionLocal
from models.entities import Participant
from services.capture_service import (
    CaptureConflictError,
    CaptureNotFoundError,
    create_log_record,
    create_participant_record,
    create_session_record,
    record_media_chunk,
)

rtms_ingest_api = Blueprint("rtms_ingest_api", __name__, url_prefix="/api/rtms")


def _require_api_token():
    expected = get_capture_api_token()
    if not expected:
        return None

    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        provided = header.split(" ", 1)[1].strip()
        if provided == expected:
            return None

    return (
        jsonify({"error": "unauthorized", "details": "Invalid or missing API token"}),
        HTTPStatus.UNAUTHORIZED,
    )


@rtms_ingest_api.before_request
def enforce_authentication():
    maybe_response = _require_api_token()
    if maybe_response:
        return maybe_response


def _get_hub():
    hub = current_app.config.get("RTMS_HUB")
    if hub is None:
        raise RuntimeError("RTMS hub not initialised")
    return hub


@rtms_ingest_api.route("/sessions", methods=["POST"])
def create_rtms_session():
    payload = request.get_json(silent=True) or {}

    meeting_uuid = payload.get("meeting_uuid")
    stream_id = payload.get("stream_id")

    if not meeting_uuid:
        return (
            jsonify({"error": "missing_meeting_uuid", "details": "meeting_uuid is required"}),
            HTTPStatus.BAD_REQUEST,
        )

    facilitator_id = payload.get("host_id") or "zoom_rtms"
    locale = payload.get("locale")
    device_kind = payload.get("device_kind") or "zoom_rtms"

    session_record = create_session_record(
        facilitator_id=facilitator_id,
        consent_at=datetime.now(timezone.utc),
        device_kind=device_kind,
        locale=locale,
    )

    log_payload: dict[str, Any] = {
        "meeting_uuid": meeting_uuid,
    }
    if stream_id:
        log_payload["stream_id"] = stream_id
    if payload.get("topic"):
        log_payload["topic"] = payload["topic"]

    create_log_record(
        session_id=session_record["id"],
        log_type="rtms",
        status="started",
        message=json.dumps(log_payload),
    )

    return (
        jsonify({"session_id": session_record["id"], "meeting_uuid": meeting_uuid}),
        HTTPStatus.CREATED,
    )


def _get_participant_by_device(session_id: str, device_id: str) -> dict | None:
    with SessionLocal() as session:
        participant = (
            session.query(Participant)
            .filter(Participant.session_id == session_id, Participant.device_id == device_id)
            .one_or_none()
        )
        if participant:
            return participant.to_dict()
        return None


@rtms_ingest_api.route("/sessions/<session_id>/participants", methods=["POST"])
def ensure_participant(session_id: str):
    payload = request.get_json(silent=True) or {}

    device_id = payload.get("zoom_user_id")
    display_name = payload.get("display_name")
    status = payload.get("status") or "active"

    if not device_id:
        return (
            jsonify({"error": "missing_zoom_user_id", "details": "zoom_user_id is required"}),
            HTTPStatus.BAD_REQUEST,
        )

    existing = _get_participant_by_device(session_id, device_id)
    if existing:
        return jsonify({"participant": existing, "created": False}), HTTPStatus.OK

    try:
        participant = create_participant_record(
            session_id=session_id,
            device_id=device_id,
            status=status,
        )
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND

    if display_name:
        create_log_record(
            session_id=session_id,
            log_type="rtms_participant",
            status="info",
            message=json.dumps({"device_id": device_id, "display_name": display_name}),
        )

    return jsonify({"participant": participant, "created": True}), HTTPStatus.CREATED


@rtms_ingest_api.route("/sessions/<session_id>/chunks", methods=["POST"])
def record_rtms_chunk(session_id: str):
    payload = request.get_json(silent=True) or {}

    storage_key = payload.get("storage_key")
    checksum = payload.get("checksum")
    duration_ms = payload.get("duration_ms")
    sequence_no = payload.get("sequence_no")
    participant_device_id = payload.get("participant_device_id")

    missing = [
        field
        for field, value in (
            ("storage_key", storage_key),
            ("checksum", checksum),
            ("duration_ms", duration_ms),
            ("sequence_no", sequence_no),
        )
        if value is None
    ]
    if missing:
        return (
            jsonify({"error": "missing_fields", "details": f"Missing fields: {', '.join(missing)}"}),
            HTTPStatus.BAD_REQUEST,
        )

    participant_id = None
    if participant_device_id:
        participant = _get_participant_by_device(session_id, participant_device_id)
        if participant is None:
            return (
                jsonify(
                    {
                        "error": "participant_not_found",
                        "details": f"Participant {participant_device_id} not registered for session {session_id}",
                    }
                ),
                HTTPStatus.NOT_FOUND,
            )
        participant_id = participant["id"]

    try:
        chunk = record_media_chunk(
            session_id=session_id,
            participant_id=participant_id,
            sequence_no=int(sequence_no),
            checksum=checksum,
            duration_ms=int(duration_ms),
            storage_key=storage_key,
        )
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND
    except CaptureConflictError as exc:
        return jsonify({"error": "conflict", "details": str(exc)}), HTTPStatus.CONFLICT

    return jsonify({"chunk": chunk}), HTTPStatus.CREATED


@rtms_ingest_api.route("/streams/<session_id>/frames", methods=["POST"])
def receive_realtime_frame(session_id: str):
    """Broadcast realtime RTMS payloads to websocket clients."""
    payload = request.get_json(silent=True) or {}
    payload.setdefault("sessionId", session_id)
    _get_hub().broadcast(payload)
    return jsonify({"status": "ok"}), HTTPStatus.ACCEPTED
