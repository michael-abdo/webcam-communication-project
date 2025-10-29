"""Phase 1 capture API endpoints."""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from datetime import datetime, timezone
from http import HTTPStatus
import json

from flask import Blueprint, current_app, jsonify, request
from werkzeug.datastructures import FileStorage

from src.services.capture_service import (
    CaptureConflictError,
    CaptureNotFoundError,
    create_participant_record,
    create_session_record,
    get_session_record,
    list_recent_sessions,
    list_session_chunks,
    record_media_chunk,
    upsert_transcript_record,
    create_log_record,
    list_session_logs,
)

from src.config import get_capture_api_token
from src.streaming.s3_handler import upload_chunk_file, upload_artifact_file, generate_download_url
from src.telemetry import metrics
from src.services.video_state import video_sessions, test_video_links

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

    upload_start = datetime.now(timezone.utc)
    try:
        storage_key = upload_chunk_file(
            session_id=session_id,
            file_obj=media.stream,
            content_type=content_type,
            sequence_no=sequence_no,
            extension=extension,
        )
    except Exception as exc:  # noqa: BLE001
        metrics().incr("phase1.chunk.failed")
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
        metrics().incr("phase1.chunk.invalid_session")
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND
    except CaptureConflictError as exc:
        metrics().incr("phase1.chunk.conflict")
        return jsonify({"error": "conflict", "details": str(exc)}), HTTPStatus.CONFLICT

    elapsed_ms = max(1, int((datetime.now(timezone.utc) - upload_start).total_seconds() * 1000))
    metrics().incr("phase1.chunk.uploaded")
    metrics().timing("phase1.chunk.upload_latency_ms", elapsed_ms)
    metrics().timing("phase1.chunk.duration_ms", duration_ms)

    current_app.logger.info(
        "phase1.chunk.persisted",
        extra={
            "session_id": session_id,
            "participant_id": participant_id,
            "sequence_no": sequence_no,
            "duration_ms": duration_ms,
            "content_length": metadata.get("content_length"),
        },
    )

    return jsonify(chunk), HTTPStatus.ACCEPTED


@capture_api.route("/sessions/<session_id>/transcript", methods=["POST"])
def upload_transcript(session_id: str):
    media: FileStorage | None = request.files.get("media")

    if media:
        metadata_raw = request.form.get("metadata")
        if not metadata_raw:
            return (
                jsonify({"error": "missing_metadata", "details": "metadata field is required"}),
                HTTPStatus.BAD_REQUEST,
            )
        try:
            metadata = json.loads(metadata_raw)
        except json.JSONDecodeError:
            return (
                jsonify({"error": "invalid_metadata", "details": "metadata must be valid JSON"}),
                HTTPStatus.BAD_REQUEST,
            )
    else:
        metadata = request.get_json(silent=True) or {}

    status = metadata.get("status")
    if not status:
        return (
            jsonify({"error": "missing_fields", "details": "status is required"}),
            HTTPStatus.BAD_REQUEST,
        )

    storage_key = metadata.get("storage_key")
    mime_type = metadata.get("mime_type")
    generated_at = metadata.get("generated_at")
    source = metadata.get("source")

    if media:
        content_type = mime_type or media.mimetype
        extension = metadata.get("file_extension")
        try:
            storage_key = upload_artifact_file(
                session_id=session_id,
                file_obj=media.stream,
                content_type=content_type,
                category="transcripts",
                extension=extension,
            )
        except Exception as exc:  # noqa: BLE001
            current_app.logger.exception("phase1.transcript.upload_failed", extra={"session_id": session_id})
            return (
                jsonify({"error": "upload_failed", "details": str(exc)}),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        mime_type = content_type
    elif not storage_key:
        return (
            jsonify({"error": "missing_fields", "details": "storage_key or media file required"}),
            HTTPStatus.BAD_REQUEST,
        )

    generated_dt = None
    if generated_at:
        try:
            generated_dt = _parse_datetime(generated_at, "generated_at")
        except ValueError as exc:
            return jsonify({"error": "invalid_datetime", "details": str(exc)}), HTTPStatus.BAD_REQUEST

    transcript = upsert_transcript_record(
        session_id=session_id,
        status=status,
        storage_key=storage_key,
        mime_type=mime_type,
        generated_at=generated_dt,
        source=source,
    )
    transcript["download_url"] = (
        generate_download_url(transcript.get("storage_key")) if transcript.get("storage_key") else None
    )
    metrics().incr("phase1.transcript.updated")
    return jsonify(transcript), HTTPStatus.OK


@capture_api.route("/sessions/<session_id>/logs", methods=["POST"])
def upload_log(session_id: str):
    media: FileStorage | None = request.files.get("media")

    if media:
        metadata_raw = request.form.get("metadata")
        if not metadata_raw:
            return (
                jsonify({"error": "missing_metadata", "details": "metadata field is required"}),
                HTTPStatus.BAD_REQUEST,
            )
        try:
            metadata = json.loads(metadata_raw)
        except json.JSONDecodeError:
            return (
                jsonify({"error": "invalid_metadata", "details": "metadata must be valid JSON"}),
                HTTPStatus.BAD_REQUEST,
            )
    else:
        metadata = request.get_json(silent=True) or {}

    status = metadata.get("status")
    log_type = metadata.get("log_type", "capture")
    message = metadata.get("message")
    recorded_at = metadata.get("recorded_at")
    storage_key = metadata.get("storage_key")
    mime_type = metadata.get("mime_type")

    if not status:
        return (
            jsonify({"error": "missing_fields", "details": "status is required"}),
            HTTPStatus.BAD_REQUEST,
        )

    if media:
        content_type = mime_type or media.mimetype
        extension = metadata.get("file_extension") or "log"
        try:
            storage_key = upload_artifact_file(
                session_id=session_id,
                file_obj=media.stream,
                content_type=content_type,
                category="logs",
                extension=extension,
            )
        except Exception as exc:  # noqa: BLE001
            current_app.logger.exception("phase1.log.upload_failed", extra={"session_id": session_id})
            return (
                jsonify({"error": "upload_failed", "details": str(exc)}),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
    elif not storage_key:
        return (
            jsonify({"error": "missing_fields", "details": "storage_key or media file required"}),
            HTTPStatus.BAD_REQUEST,
        )

    recorded_dt = None
    if recorded_at:
        try:
            recorded_dt = _parse_datetime(recorded_at, "recorded_at")
        except ValueError as exc:
            return jsonify({"error": "invalid_datetime", "details": str(exc)}), HTTPStatus.BAD_REQUEST

    log_entry = create_log_record(
        session_id=session_id,
        log_type=log_type,
        status=status,
        storage_key=storage_key,
        message=message,
        recorded_at=recorded_dt,
    )
    log_entry["download_url"] = (
        generate_download_url(log_entry.get("storage_key")) if log_entry.get("storage_key") else None
    )
    metrics().incr("phase1.log.updated")
    return jsonify(log_entry), HTTPStatus.CREATED


@capture_api.route("/sessions/<session_id>", methods=["GET"])
def get_session(session_id: str):
    try:
        session_record = get_session_record(session_id)
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND

    chunks_with_links = []
    for chunk in session_record.get("chunks", []):
        download_url = generate_download_url(chunk.get("storage_key"))
        chunk_copy = dict(chunk)
        chunk_copy["download_url"] = download_url
        chunk_copy.setdefault("transcript_status", "not_available")
        chunk_copy.setdefault("log_status", "not_available")
        chunks_with_links.append(chunk_copy)

    transcript = session_record.get("transcript")
    transcript_status = "not_available"
    if transcript:
        transcript_status = (transcript.get("status") or "unknown").lower()
        transcript["download_url"] = (
            generate_download_url(transcript.get("storage_key"))
            if transcript.get("storage_key")
            else None
        )

    logs_with_links = []
    log_status = "not_available"
    log_statuses: list[str] = []
    for log in session_record.get("logs", []):
        entry = dict(log)
        entry["download_url"] = (
            generate_download_url(log.get("storage_key")) if log.get("storage_key") else None
        )
        logs_with_links.append(entry)
        if log.get("status"):
            log_statuses.append(log["status"].lower())

    if log_statuses:
        if any(status in {"failed", "error"} for status in log_statuses):
            log_status = "failed"
        elif any(status in {"attention_required", "processing", "pending"} for status in log_statuses):
            log_status = "attention_required"
        elif any(status == "completed" for status in log_statuses):
            log_status = "completed"
        else:
            log_status = log_statuses[0]

    session_record["chunks"] = chunks_with_links
    session_record["transcript"] = transcript
    session_record["logs"] = logs_with_links
    session_record["transcript_status"] = transcript_status
    session_record["log_status"] = log_status

    alert_state = "ok"
    if (
        not chunks_with_links
        or transcript_status in {"failed", "attention_required"}
        or log_status in {"failed", "attention_required"}
    ):
        alert_state = "attention_required"
    session_record["alert_state"] = alert_state

    return jsonify(session_record), HTTPStatus.OK

@capture_api.route("/sessions/<session_id>/chunks/<int:sequence_no>/download", methods=["GET"])
def get_chunk_download(session_id: str, sequence_no: int):
    try:
        chunks = list_session_chunks(session_id)
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND

    for chunk in chunks:
        if chunk.get("sequence_no") == sequence_no:
            url = generate_download_url(chunk.get("storage_key"))
            if not url:
                return jsonify({"error": "unavailable", "details": "Download URL could not be generated"}), HTTPStatus.INTERNAL_SERVER_ERROR
            metrics().incr("phase1.chunk.download_requested")
            return jsonify({"url": url, "expires_in": 3600}), HTTPStatus.OK

    return jsonify({"error": "not_found", "details": "Chunk not found"}), HTTPStatus.NOT_FOUND


@capture_api.route("/sessions/<session_id>/transcript/download", methods=["GET"])
def get_transcript_download(session_id: str):
    try:
        session_record = get_session_record(session_id)
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND

    transcript = session_record.get("transcript")
    if not transcript or not transcript.get("storage_key"):
        return jsonify({"error": "not_found", "details": "Transcript not available"}), HTTPStatus.NOT_FOUND

    url = generate_download_url(transcript.get("storage_key"))
    if not url:
        return (
            jsonify({"error": "unavailable", "details": "Download URL could not be generated"}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
    metrics().incr("phase1.transcript.download_requested")
    return jsonify({"url": url, "expires_in": 3600}), HTTPStatus.OK


@capture_api.route("/sessions/<session_id>/logs/<log_id>/download", methods=["GET"])
def get_log_download(session_id: str, log_id: str):
    try:
        logs = list_session_logs(session_id)
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND

    for log in logs:
        if log.get("id") == log_id:
            if not log.get("storage_key"):
                return jsonify({"error": "not_found", "details": "Log has no storage backing"}), HTTPStatus.NOT_FOUND
            url = generate_download_url(log.get("storage_key"))
            if not url:
                return (
                    jsonify({"error": "unavailable", "details": "Download URL could not be generated"}),
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                )
            metrics().incr("phase1.log.download_requested")
            return jsonify({"url": url, "expires_in": 3600}), HTTPStatus.OK

    return jsonify({"error": "not_found", "details": "Log not found"}), HTTPStatus.NOT_FOUND
