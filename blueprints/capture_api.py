"""Phase 1 capture API endpoints."""

from __future__ import annotations

from datetime import datetime
from http import HTTPStatus

from flask import Blueprint, current_app, jsonify, request

from services.capture_service import (
    CaptureConflictError,
    CaptureNotFoundError,
    create_participant_record,
    create_session_record,
    get_session_record,
    list_recent_sessions,
    record_media_chunk,
)

from config import get_capture_api_token

capture_api = Blueprint("capture_api", __name__, url_prefix="/api")


def _parse_datetime(value: str, field_name: str) -> datetime:
    try:
        cleaned = value.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Invalid datetime format for {field_name}") from exc


def _require_api_token():
    """Enforce facilitator token when CAPTURE_API_TOKEN is configured."""
    expected = get_capture_api_token()
    if not expected:
        return None

    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return jsonify(
            {
                "error": "unauthorized",
                "details": "Authorization header with Bearer token required",
            }
        ), HTTPStatus.UNAUTHORIZED

    provided = header.split(" ", 1)[1].strip()
    if provided != expected:
        return jsonify({"error": "forbidden", "details": "Invalid facilitator token"}), HTTPStatus.FORBIDDEN

    return None


@capture_api.before_request
def enforce_authentication():
    maybe_response = _require_api_token()
    if maybe_response:
        return maybe_response


@capture_api.route("/sessions", methods=["GET"])
def list_sessions():
    limit = request.args.get("limit", default=20, type=int)
    limit = max(1, min(limit, 100))
    sessions = list_recent_sessions(limit=limit)
    return jsonify({"sessions": sessions, "count": len(sessions)}), HTTPStatus.OK


@capture_api.route("/sessions", methods=["POST"])
def create_session():
    payload = request.get_json(silent=True) or {}

    facilitator_id = payload.get("facilitator_id")
    consent_at = payload.get("consent_at")
    device_kind = payload.get("device_kind")
    locale = payload.get("locale")

    missing_fields = [
        field
        for field, value in (
            ("facilitator_id", facilitator_id),
            ("consent_at", consent_at),
            ("device_kind", device_kind),
        )
        if not value
    ]
    if missing_fields:
        return (
            jsonify(
                {
                    "error": "missing_fields",
                    "details": f"Missing required fields: {', '.join(missing_fields)}",
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        consent_at_dt = _parse_datetime(consent_at, "consent_at")
    except ValueError as exc:
        return jsonify({"error": "invalid_datetime", "details": str(exc)}), HTTPStatus.BAD_REQUEST

    session_record = create_session_record(
        facilitator_id=facilitator_id,
        consent_at=consent_at_dt,
        device_kind=device_kind,
        locale=locale,
    )

    current_app.logger.info(
        "phase1.session.created",
        extra={
            "session_id": session_record["id"],
            "device_kind": device_kind,
        },
    )

    return jsonify(session_record), HTTPStatus.CREATED


@capture_api.route("/sessions/<session_id>/participants", methods=["POST"])
def register_participant(session_id: str):
    payload = request.get_json(silent=True) or {}

    device_id = payload.get("device_id")
    status = payload.get("status")
    last_heartbeat_at = payload.get("last_heartbeat_at")

    missing_fields = [
        field for field, value in (("device_id", device_id), ("status", status)) if not value
    ]
    if missing_fields:
        return (
            jsonify(
                {
                    "error": "missing_fields",
                    "details": f"Missing required fields: {', '.join(missing_fields)}",
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    heartbeat_dt = None
    if last_heartbeat_at:
        try:
            heartbeat_dt = _parse_datetime(last_heartbeat_at, "last_heartbeat_at")
        except ValueError as exc:
            return (
                jsonify({"error": "invalid_datetime", "details": str(exc)}),
                HTTPStatus.BAD_REQUEST,
            )

    try:
        participant = create_participant_record(
            session_id=session_id,
            device_id=device_id,
            status=status,
            last_heartbeat_at=heartbeat_dt,
        )
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND

    current_app.logger.info(
        "phase1.participant.registered",
        extra={
            "session_id": session_id,
            "participant_id": participant["id"],
            "status": participant["status"],
        },
    )

    return jsonify(participant), HTTPStatus.CREATED


@capture_api.route("/sessions/<session_id>/chunks", methods=["POST"])
def record_chunk(session_id: str):
    payload = request.get_json(silent=True) or {}

    sequence_no = payload.get("sequence_no")
    checksum = payload.get("checksum")
    duration_ms = payload.get("duration_ms")
    storage_key = payload.get("storage_key")
    participant_id = payload.get("participant_id")
    stored_at = payload.get("stored_at")

    missing_fields = [
        field
        for field, value in (
            ("sequence_no", sequence_no),
            ("checksum", checksum),
            ("duration_ms", duration_ms),
            ("storage_key", storage_key),
        )
        if value in (None, "")
    ]
    if missing_fields:
        return (
            jsonify(
                {
                    "error": "missing_fields",
                    "details": f"Missing required fields: {', '.join(missing_fields)}",
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    if not isinstance(sequence_no, int) or sequence_no < 0:
        return (
            jsonify(
                {"error": "invalid_sequence", "details": "sequence_no must be a non-negative integer"}
            ),
            HTTPStatus.BAD_REQUEST,
        )

    if not isinstance(duration_ms, int) or duration_ms <= 0:
        return (
            jsonify(
                {"error": "invalid_duration", "details": "duration_ms must be a positive integer"}
            ),
            HTTPStatus.BAD_REQUEST,
        )

    stored_at_dt = None
    if stored_at:
        try:
            stored_at_dt = _parse_datetime(stored_at, "stored_at")
        except ValueError as exc:
            return (
                jsonify({"error": "invalid_datetime", "details": str(exc)}),
                HTTPStatus.BAD_REQUEST,
            )

    try:
        chunk = record_media_chunk(
            session_id=session_id,
            sequence_no=sequence_no,
            checksum=checksum,
            duration_ms=duration_ms,
            storage_key=storage_key,
            participant_id=participant_id,
            stored_at=stored_at_dt,
        )
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND
    except CaptureConflictError as exc:
        return jsonify({"error": "conflict", "details": str(exc)}), HTTPStatus.CONFLICT

    current_app.logger.info(
        "phase1.chunk.persisted",
        extra={
            "session_id": session_id,
            "participant_id": participant_id,
            "sequence_no": sequence_no,
            "duration_ms": duration_ms,
        },
    )

    return jsonify(chunk), HTTPStatus.ACCEPTED


@capture_api.route("/sessions/<session_id>", methods=["GET"])
def get_session(session_id: str):
    try:
        session_record = get_session_record(session_id)
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND

    return jsonify(session_record), HTTPStatus.OK
