"""API endpoints for Zoom RTMS ingestion service."""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from datetime import datetime, timezone
from http import HTTPStatus
import json
from typing import Any

from flask import Blueprint, jsonify, request, current_app

from src.config import get_capture_api_token
from src.models import SessionLocal
from src.models.entities import Participant
from src.services.capture_service import (
    CaptureConflictError,
    CaptureNotFoundError,
    create_log_record,
    create_participant_record,
    create_session_record,
    create_transcription_segment,
    create_zoom_meeting,
    get_rtms_health_status,
    get_session_transcription,
    record_media_chunk,
    record_rtms_health_check,
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
    
    # Create zoom meeting record if we have meeting UUID
    if meeting_uuid:
        try:
            zoom_meeting = create_zoom_meeting(
                meeting_uuid=meeting_uuid,
                session_id=session_record["id"],
                host_id=payload.get("host_id") or facilitator_id,
                topic=payload.get("topic"),
                start_time=datetime.now(timezone.utc),
                rtms_stream_id=stream_id,
            )
            session_record["zoom_meeting_id"] = zoom_meeting["id"]
        except Exception as exc:
            # Log error but don't fail session creation
            create_log_record(
                session_id=session_record["id"],
                log_type="rtms",
                status="error",
                message=f"Failed to create zoom_meeting: {str(exc)}",
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
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not payload:
        current_app.logger.warning(
            "rtms.ingest.invalid_payload",
            extra={"session_id": session_id, "payload_type": type(payload).__name__},
        )
        return (
            jsonify({"error": "invalid_payload", "details": "Expected non-empty JSON object"}),
            HTTPStatus.BAD_REQUEST,
        )

    if "type" not in payload:
        current_app.logger.warning(
            "rtms.ingest.missing_type",
            extra={"session_id": session_id, "keys": list(payload.keys())},
        )
        return (
            jsonify({"error": "missing_type", "details": "Payload must include a type field"}),
            HTTPStatus.BAD_REQUEST,
        )

    payload.setdefault("sessionId", session_id)
    if "streamId" not in payload and "stream_id" in payload:
        payload["streamId"] = payload["stream_id"]

    try:
        _get_hub().broadcast(payload)
    except Exception:  # pragma: no cover - hub already logs failures
        current_app.logger.exception(
            "rtms.ingest.broadcast_failed",
            extra={"session_id": session_id, "payload_type": payload.get("type")},
        )
        return (
            jsonify({"error": "broadcast_failed", "details": "Unable to notify RTMS clients"}),
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    return jsonify({"status": "ok"}), HTTPStatus.ACCEPTED


@rtms_ingest_api.route("/transcription/segments", methods=["POST"])
def add_transcription_segment():
    """Add a transcription segment."""
    payload = request.get_json(silent=True) or {}
    
    # Required fields
    session_id = payload.get("session_id")
    text = payload.get("text")
    start_time = payload.get("start_time")
    end_time = payload.get("end_time")
    
    if not session_id:
        return jsonify({"error": "missing_field", "details": "session_id is required"}), HTTPStatus.BAD_REQUEST
    
    if not text:
        return jsonify({"error": "missing_field", "details": "text is required"}), HTTPStatus.BAD_REQUEST
    
    if start_time is None:
        return jsonify({"error": "missing_field", "details": "start_time is required"}), HTTPStatus.BAD_REQUEST
        
    if end_time is None:
        return jsonify({"error": "missing_field", "details": "end_time is required"}), HTTPStatus.BAD_REQUEST
    
    # Optional fields
    participant_id = payload.get("participant_id")
    confidence = payload.get("confidence")
    language = payload.get("language")
    
    try:
        segment = create_transcription_segment(
            session_id=session_id,
            text=text,
            start_time=float(start_time),
            end_time=float(end_time),
            participant_id=participant_id,
            confidence=confidence,
            language=language,
        )
        return jsonify(segment), HTTPStatus.CREATED
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND


@rtms_ingest_api.route("/sessions/<session_id>/transcription", methods=["GET"])
def get_transcription(session_id: str):
    """Get transcription segments for a session."""
    limit = request.args.get("limit", type=int)
    
    try:
        segments = get_session_transcription(session_id, limit=limit)
        return jsonify({"session_id": session_id, "segments": segments}), HTTPStatus.OK
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND


@rtms_ingest_api.route("/health", methods=["POST"])
def record_health_check():
    """Record an RTMS health check."""
    payload = request.get_json(silent=True) or {}
    
    # Required fields
    meeting_id = payload.get("meeting_id")
    stream_id = payload.get("stream_id")
    status = payload.get("status")
    
    if not meeting_id:
        return jsonify({"error": "missing_field", "details": "meeting_id is required"}), HTTPStatus.BAD_REQUEST
    
    if not stream_id:
        return jsonify({"error": "missing_field", "details": "stream_id is required"}), HTTPStatus.BAD_REQUEST
    
    if not status:
        return jsonify({"error": "missing_field", "details": "status is required"}), HTTPStatus.BAD_REQUEST
    
    # Optional fields
    latency_ms = payload.get("latency_ms")
    frames_processed = payload.get("frames_processed", 0)
    errors = payload.get("errors")
    
    try:
        health_check = record_rtms_health_check(
            meeting_id=meeting_id,
            stream_id=stream_id,
            status=status,
            checked_at=datetime.now(timezone.utc),
            latency_ms=latency_ms,
            frames_processed=frames_processed,
            errors=errors,
        )
        return jsonify(health_check), HTTPStatus.CREATED
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND


@rtms_ingest_api.route("/health/<stream_id>", methods=["GET"])
def get_health_status(stream_id: str):
    """Get recent health status for a stream."""
    limit = request.args.get("limit", 10, type=int)
    
    health_checks = get_rtms_health_status(stream_id, limit=limit)
    return jsonify({"stream_id": stream_id, "health_checks": health_checks}), HTTPStatus.OK
