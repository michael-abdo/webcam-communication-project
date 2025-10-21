"""Phase 1 capture API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from http import HTTPStatus
import json

from flask import Blueprint, current_app, jsonify, request
from werkzeug.datastructures import FileStorage

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
from streaming.s3_handler import upload_chunk_file
from services.video_state import video_sessions, test_video_links

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
    media: FileStorage | None = request.files.get("media")
    metadata_raw = request.form.get("metadata")

    if not media:
        return (
            jsonify({"error": "missing_media", "details": "Multipart field 'media' is required."}),
            HTTPStatus.BAD_REQUEST,
        )

    if not metadata_raw:
        return (
            jsonify({"error": "missing_metadata", "details": "Multipart field 'metadata' is required."}),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        metadata = json.loads(metadata_raw)
    except json.JSONDecodeError:
        return (
            jsonify({"error": "invalid_metadata", "details": "metadata field must be valid JSON."}),
            HTTPStatus.BAD_REQUEST,
        )

    sequence_no = metadata.get("sequence_no")
    checksum = metadata.get("checksum")
    duration_ms = metadata.get("duration_ms")
    participant_id = metadata.get("participant_id")
    stored_at = metadata.get("stored_at")
    extension = metadata.get("file_extension")
    content_type_override = metadata.get("mime_type")

    required_missing = [
        field
        for field, value in (
            ("sequence_no", sequence_no),
            ("checksum", checksum),
            ("duration_ms", duration_ms),
        )
        if value in (None, "")
    ]
    if required_missing:
        return (
            jsonify(
                {
                    "error": "missing_fields",
                    "details": f"Missing required metadata fields: {', '.join(required_missing)}",
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        sequence_no = int(sequence_no)
    except (TypeError, ValueError):
        return (
            jsonify(
                {"error": "invalid_sequence", "details": "sequence_no must be an integer."}
            ),
            HTTPStatus.BAD_REQUEST,
        )

    if sequence_no < 0:
        return (
            jsonify(
                {"error": "invalid_sequence", "details": "sequence_no must be non-negative."}
            ),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        duration_ms = int(duration_ms)
    except (TypeError, ValueError):
        return (
            jsonify({"error": "invalid_duration", "details": "duration_ms must be an integer."}),
            HTTPStatus.BAD_REQUEST,
        )

    if duration_ms <= 0:
        return (
            jsonify({"error": "invalid_duration", "details": "duration_ms must be positive."}),
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

    content_type = content_type_override or media.mimetype
    test_session_id = metadata.get("test_session_id")

    # Maintain legacy session mappings for test dashboards
    default_start = stored_at_dt or datetime.now(timezone.utc)
    session_state = video_sessions.setdefault(
        session_id,
        {
            "video_session_id": session_id,
            "start_time": default_start,
            "chunks_uploaded": 0,
            "status": "active",
        },
    )
    session_state["chunks_uploaded"] = session_state.get("chunks_uploaded", 0) + 1
    session_state["last_chunk_at"] = stored_at_dt or datetime.now(timezone.utc)
    if test_session_id:
        session_state["test_session_id"] = test_session_id
        test_video_links[test_session_id] = session_id

    try:
        storage_key = upload_chunk_file(
            session_id=session_id,
            file_obj=media.stream,
            content_type=content_type,
            sequence_no=sequence_no,
            extension=extension,
        )
    except Exception as exc:  # noqa: BLE001
        current_app.logger.exception("phase1.chunk.upload_failed", extra={"session_id": session_id})
        return (
            jsonify({"error": "upload_failed", "details": str(exc)}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
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
