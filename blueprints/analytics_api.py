"""API endpoints for meeting analytics."""

from __future__ import annotations

from datetime import datetime, timezone
from http import HTTPStatus

from flask import Blueprint, jsonify, request

from config import get_capture_api_token
from models import SessionLocal
from models.entities import ZoomMeeting
from services.capture_service import (
    CaptureNotFoundError,
    create_meeting_analytics,
    get_meeting_analytics,
)

analytics_api = Blueprint("analytics_api", __name__, url_prefix="/api/analytics")


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


@analytics_api.before_request
def enforce_authentication():
    maybe_response = _require_api_token()
    if maybe_response:
        return maybe_response


@analytics_api.route("/meetings/<meeting_id>", methods=["GET"])
def get_analytics(meeting_id: str):
    """Get analytics for a specific meeting."""
    try:
        analytics = get_meeting_analytics(meeting_id)
        return jsonify(analytics), HTTPStatus.OK
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND


@analytics_api.route("/compute/<meeting_id>", methods=["POST"])
def compute_analytics(meeting_id: str):
    """Compute or update analytics for a meeting."""
    payload = request.get_json(silent=True) or {}
    
    # Required fields
    total_duration_seconds = payload.get("total_duration_seconds")
    participant_count = payload.get("participant_count")
    
    if total_duration_seconds is None:
        return jsonify({"error": "missing_field", "details": "total_duration_seconds is required"}), HTTPStatus.BAD_REQUEST
    
    if participant_count is None:
        return jsonify({"error": "missing_field", "details": "participant_count is required"}), HTTPStatus.BAD_REQUEST
    
    # Optional fields
    talk_time_distribution = payload.get("talk_time_distribution")
    interruption_count = payload.get("interruption_count", 0)
    avg_speech_pace = payload.get("avg_speech_pace")
    computed_at_str = payload.get("computed_at")
    
    # Validate talk_time_distribution is a dict if provided
    if talk_time_distribution is not None and not isinstance(talk_time_distribution, dict):
        return jsonify({"error": "invalid_field", "details": "talk_time_distribution must be an object"}), HTTPStatus.BAD_REQUEST
    
    computed_at = datetime.now(timezone.utc)
    if computed_at_str:
        try:
            computed_at = datetime.fromisoformat(computed_at_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return jsonify({"error": "invalid_field", "details": "computed_at must be in ISO format"}), HTTPStatus.BAD_REQUEST
    
    try:
        analytics = create_meeting_analytics(
            meeting_id=meeting_id,
            total_duration_seconds=total_duration_seconds,
            participant_count=participant_count,
            computed_at=computed_at,
            talk_time_distribution=talk_time_distribution,
            interruption_count=interruption_count,
            avg_speech_pace=avg_speech_pace,
        )
        return jsonify(analytics), HTTPStatus.CREATED
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND


@analytics_api.route("/meetings", methods=["GET"])
def list_recent_analytics():
    """List recent analytics records."""
    limit = request.args.get("limit", 100, type=int)
    since = request.args.get("since")  # ISO timestamp
    
    with SessionLocal() as session:
        query = (
            session.query(ZoomMeeting)
            .join(ZoomMeeting.analytics)
            .order_by(ZoomMeeting.created_at.desc())
        )
        
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                query = query.filter(ZoomMeeting.created_at >= since_dt)
            except (ValueError, AttributeError):
                return jsonify({"error": "invalid_parameter", "details": "since must be in ISO format"}), HTTPStatus.BAD_REQUEST
        
        meetings = query.limit(limit).all()
        
        results = []
        for meeting in meetings:
            if meeting.analytics:
                result = meeting.analytics.to_dict()
                result["meeting"] = {
                    "id": meeting.id,
                    "meeting_uuid": meeting.meeting_uuid,
                    "topic": meeting.topic,
                    "start_time": meeting.start_time.isoformat(),
                    "end_time": meeting.end_time.isoformat() if meeting.end_time else None,
                }
                results.append(result)
        
        return jsonify(results), HTTPStatus.OK