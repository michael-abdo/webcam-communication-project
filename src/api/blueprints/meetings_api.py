"""API endpoints for Zoom meetings management."""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from datetime import datetime, timezone
from http import HTTPStatus

from flask import Blueprint, jsonify, request

from src.config import get_capture_api_token
from src.models import SessionLocal
from src.models.entities import ZoomMeeting, ZoomParticipant
from src.services.capture_service import (
    CaptureConflictError,
    CaptureNotFoundError,
    create_zoom_meeting,
    create_zoom_participant,
    get_zoom_meeting,
    update_participant_leave_time,
    update_zoom_meeting_end_time,
)

meetings_api = Blueprint("meetings_api", __name__, url_prefix="/api/meetings")


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


@meetings_api.before_request
def enforce_authentication():
    maybe_response = _require_api_token()
    if maybe_response:
        return maybe_response


@meetings_api.route("", methods=["POST"])
def create_meeting():
    """Create a new Zoom meeting record."""
    payload = request.get_json(silent=True) or {}
    
    # Required fields
    meeting_uuid = payload.get("meeting_uuid")
    session_id = payload.get("session_id")
    host_id = payload.get("host_id")
    
    if not meeting_uuid:
        return jsonify({"error": "missing_field", "details": "meeting_uuid is required"}), HTTPStatus.BAD_REQUEST
    
    if not session_id:
        return jsonify({"error": "missing_field", "details": "session_id is required"}), HTTPStatus.BAD_REQUEST
        
    if not host_id:
        return jsonify({"error": "missing_field", "details": "host_id is required"}), HTTPStatus.BAD_REQUEST
    
    # Optional fields
    topic = payload.get("topic")
    start_time_str = payload.get("start_time")
    rtms_stream_id = payload.get("rtms_stream_id")
    
    start_time = None
    if start_time_str:
        try:
            start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return jsonify({"error": "invalid_field", "details": "start_time must be in ISO format"}), HTTPStatus.BAD_REQUEST
    
    try:
        meeting = create_zoom_meeting(
            meeting_uuid=meeting_uuid,
            session_id=session_id,
            host_id=host_id,
            topic=topic,
            start_time=start_time,
            rtms_stream_id=rtms_stream_id,
        )
        return jsonify(meeting), HTTPStatus.CREATED
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND
    except CaptureConflictError as exc:
        return jsonify({"error": "conflict", "details": str(exc)}), HTTPStatus.CONFLICT


@meetings_api.route("/<meeting_id>", methods=["GET"])
def get_meeting(meeting_id: str):
    """Get a meeting by ID."""
    try:
        meeting = get_zoom_meeting(meeting_id)
        return jsonify(meeting), HTTPStatus.OK
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND


@meetings_api.route("/<meeting_id>", methods=["PATCH"])
def update_meeting(meeting_id: str):
    """Update a meeting (currently only supports ending the meeting)."""
    payload = request.get_json(silent=True) or {}
    
    end_time_str = payload.get("end_time")
    
    if end_time_str:
        try:
            end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return jsonify({"error": "invalid_field", "details": "end_time must be in ISO format"}), HTTPStatus.BAD_REQUEST
        
        try:
            meeting = update_zoom_meeting_end_time(meeting_id, end_time)
            return jsonify(meeting), HTTPStatus.OK
        except CaptureNotFoundError as exc:
            return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND
    
    return jsonify({"error": "invalid_request", "details": "No valid update fields provided"}), HTTPStatus.BAD_REQUEST


@meetings_api.route("", methods=["GET"])
def list_meetings():
    """List meetings with optional filtering."""
    limit = request.args.get("limit", 100, type=int)
    session_id = request.args.get("session_id")
    
    with SessionLocal() as session:
        query = session.query(ZoomMeeting).order_by(ZoomMeeting.created_at.desc())
        
        if session_id:
            query = query.filter_by(session_id=session_id)
        
        meetings = query.limit(limit).all()
        
        return jsonify([meeting.to_dict() for meeting in meetings]), HTTPStatus.OK


@meetings_api.route("/<meeting_id>/participants", methods=["POST"])
def add_participant(meeting_id: str):
    """Add a participant to a meeting."""
    payload = request.get_json(silent=True) or {}
    
    # Required fields
    zoom_user_id = payload.get("zoom_user_id")
    join_time_str = payload.get("join_time")
    
    if not zoom_user_id:
        return jsonify({"error": "missing_field", "details": "zoom_user_id is required"}), HTTPStatus.BAD_REQUEST
        
    if not join_time_str:
        return jsonify({"error": "missing_field", "details": "join_time is required"}), HTTPStatus.BAD_REQUEST
    
    try:
        join_time = datetime.fromisoformat(join_time_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return jsonify({"error": "invalid_field", "details": "join_time must be in ISO format"}), HTTPStatus.BAD_REQUEST
    
    # Optional fields
    display_name = payload.get("display_name")
    email = payload.get("email")
    role = payload.get("role", "participant")
    
    try:
        participant = create_zoom_participant(
            meeting_id=meeting_id,
            zoom_user_id=zoom_user_id,
            join_time=join_time,
            display_name=display_name,
            email=email,
            role=role,
        )
        return jsonify(participant), HTTPStatus.CREATED
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND


@meetings_api.route("/<meeting_id>/participants", methods=["GET"])
def list_participants(meeting_id: str):
    """List all participants in a meeting."""
    with SessionLocal() as session:
        meeting = session.get(ZoomMeeting, meeting_id)
        if meeting is None:
            return jsonify({"error": "not_found", "details": f"Meeting {meeting_id} not found"}), HTTPStatus.NOT_FOUND
        
        participants = session.query(ZoomParticipant).filter_by(meeting_id=meeting_id).order_by(ZoomParticipant.join_time).all()
        
        return jsonify([participant.to_dict() for participant in participants]), HTTPStatus.OK


@meetings_api.route("/participants/<participant_id>", methods=["PATCH"])
def update_participant(participant_id: str):
    """Update a participant (currently only supports leave time)."""
    payload = request.get_json(silent=True) or {}
    
    leave_time_str = payload.get("leave_time")
    
    if leave_time_str:
        try:
            leave_time = datetime.fromisoformat(leave_time_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return jsonify({"error": "invalid_field", "details": "leave_time must be in ISO format"}), HTTPStatus.BAD_REQUEST
        
        try:
            participant = update_participant_leave_time(participant_id, leave_time)
            return jsonify(participant), HTTPStatus.OK
        except CaptureNotFoundError as exc:
            return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND
    
    return jsonify({"error": "invalid_request", "details": "No valid update fields provided"}), HTTPStatus.BAD_REQUEST