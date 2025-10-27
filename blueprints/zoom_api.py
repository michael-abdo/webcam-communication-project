"""API endpoints for Zoom meeting integration."""

from __future__ import annotations

from datetime import datetime, timezone
from http import HTTPStatus

from flask import Blueprint, jsonify, request

from config import get_capture_api_token
from services.capture_service import (
    CaptureNotFoundError,
    create_session_event,
    get_session_events,
    get_zoom_meeting,
    update_zoom_meeting,
)

zoom_api = Blueprint("zoom_api", __name__, url_prefix="/api")


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


@zoom_api.before_request
def enforce_authentication():
    maybe_response = _require_api_token()
    if maybe_response:
        return maybe_response


@zoom_api.route("/sessions/<session_id>/zoom", methods=["POST"])
def register_zoom_meeting(session_id: str):
    """Register Zoom meeting metadata plus capture worker credentials."""
    payload = request.get_json(silent=True) or {}
    
    meeting_id = payload.get("meeting_id")
    account_id = payload.get("account_id")
    access_token = payload.get("access_token")
    expires_at = payload.get("expires_at")
    capture_worker_id = payload.get("capture_worker_id")
    capture_token = payload.get("capture_token")
    capture_heartbeat_at = payload.get("capture_heartbeat_at")
    
    if not meeting_id:
        return jsonify({"error": "missing_field", "details": "meeting_id is required"}), HTTPStatus.BAD_REQUEST
        
    if not account_id:
        return jsonify({"error": "missing_field", "details": "account_id is required"}), HTTPStatus.BAD_REQUEST
    
    try:
        # Get existing zoom meeting for this session
        from models import SessionLocal
        from models.entities import ZoomMeeting, Session
        
        with SessionLocal() as db_session:
            session = db_session.query(Session).filter_by(id=session_id).first()
            if not session:
                raise CaptureNotFoundError(f"Session {session_id} not found")
                
            zoom_meeting = db_session.query(ZoomMeeting).filter_by(session_id=session_id).first()
            if not zoom_meeting:
                return jsonify({"error": "not_found", "details": "No Zoom meeting found for this session"}), HTTPStatus.NOT_FOUND
            
            # Update with capture worker information
            # In a real implementation, we would store access_token and capture_token in a vault
            # For now, we'll just store a reference
            vault_ref = f"vault://zoom/{session_id}"
            
            zoom_meeting.vault_credential_ref = vault_ref
            zoom_meeting.capture_worker_id = capture_worker_id
            zoom_meeting.capture_status = "active" if capture_worker_id else "idle"
            
            if capture_heartbeat_at:
                zoom_meeting.capture_last_heartbeat = datetime.fromisoformat(capture_heartbeat_at.replace('Z', '+00:00'))
                
            db_session.commit()
            
        return "", HTTPStatus.NO_CONTENT
        
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND
    except Exception as exc:
        return jsonify({"error": "internal_error", "details": str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR


@zoom_api.route("/sessions/<session_id>/zoom/heartbeat", methods=["POST"])
def update_capture_heartbeat(session_id: str):
    """Update capture worker heartbeat."""
    payload = request.get_json(silent=True) or {}
    
    capture_worker_id = payload.get("capture_worker_id")
    status = payload.get("status")
    heartbeat_at = payload.get("heartbeat_at")
    
    if not capture_worker_id:
        return jsonify({"error": "missing_field", "details": "capture_worker_id is required"}), HTTPStatus.BAD_REQUEST
        
    if not status:
        return jsonify({"error": "missing_field", "details": "status is required"}), HTTPStatus.BAD_REQUEST
        
    if not heartbeat_at:
        return jsonify({"error": "missing_field", "details": "heartbeat_at is required"}), HTTPStatus.BAD_REQUEST
    
    try:
        from models import SessionLocal
        from models.entities import ZoomMeeting
        
        with SessionLocal() as db_session:
            zoom_meeting = db_session.query(ZoomMeeting).filter_by(session_id=session_id).first()
            if not zoom_meeting:
                return jsonify({"error": "not_found", "details": "No Zoom meeting found for this session"}), HTTPStatus.NOT_FOUND
            
            # Verify capture worker ID matches
            if zoom_meeting.capture_worker_id != capture_worker_id:
                return jsonify({"error": "forbidden", "details": "Capture worker ID mismatch"}), HTTPStatus.FORBIDDEN
            
            # Update heartbeat
            zoom_meeting.capture_status = status
            zoom_meeting.capture_last_heartbeat = datetime.fromisoformat(heartbeat_at.replace('Z', '+00:00'))
            
            db_session.commit()
            
        return "", HTTPStatus.NO_CONTENT
        
    except Exception as exc:
        return jsonify({"error": "internal_error", "details": str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR


@zoom_api.route("/zoom-participants/<participant_id>/events", methods=["POST"])
def record_participant_event(participant_id: str):
    """Record participant events (join/leave/pause)."""
    payload = request.get_json(silent=True) or {}
    
    kind = payload.get("kind")
    occurred_at = payload.get("occurred_at")
    
    if not kind:
        return jsonify({"error": "missing_field", "details": "kind is required"}), HTTPStatus.BAD_REQUEST
        
    if not occurred_at:
        return jsonify({"error": "missing_field", "details": "occurred_at is required"}), HTTPStatus.BAD_REQUEST
    
    try:
        # Get participant and session info
        from models import SessionLocal
        from models.entities import ZoomParticipant
        
        with SessionLocal() as db_session:
            participant = db_session.query(ZoomParticipant).filter_by(id=participant_id).first()
            if not participant:
                return jsonify({"error": "not_found", "details": f"Participant {participant_id} not found"}), HTTPStatus.NOT_FOUND
            
            # Get session ID from the meeting
            session_id = participant.meeting.session_id
            
            # Create event payload
            event_payload = {
                "participant_id": participant_id,
                "zoom_user_id": participant.zoom_user_id,
                "display_name": participant.display_name,
            }
            
        # Record the event
        event_dt = datetime.fromisoformat(occurred_at.replace('Z', '+00:00'))
        create_session_event(
            session_id=session_id,
            event_type=kind,
            payload=event_payload,
            occurred_at=event_dt,
            participant_id=participant_id,
        )
        
        return "", HTTPStatus.ACCEPTED
        
    except CaptureNotFoundError as exc:
        return jsonify({"error": "not_found", "details": str(exc)}), HTTPStatus.NOT_FOUND
    except Exception as exc:
        return jsonify({"error": "internal_error", "details": str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR


@zoom_api.route("/sessions/<session_id>/transcript", methods=["GET"])
def get_session_transcript(session_id: str):
    """Get rolling transcript segments for dashboards."""
    since_sequence = request.args.get("since_sequence", type=int)
    
    try:
        from models import SessionLocal
        from models.entities import TranscriptionSegment
        
        with SessionLocal() as db_session:
            query = db_session.query(TranscriptionSegment).filter_by(session_id=session_id)
            
            # For this implementation, we'll use ID-based pagination
            # In a real system, we'd have proper sequence numbers
            if since_sequence:
                # Get segments created after the given sequence
                query = query.filter(TranscriptionSegment.id > since_sequence)
            
            segments = query.order_by(TranscriptionSegment.start_time).limit(100).all()
            
            result = []
            for i, seg in enumerate(segments):
                result.append({
                    "sequence_no": since_sequence + i + 1 if since_sequence else i + 1,
                    "speaker_id": seg.participant_id or "unknown",
                    "text": seg.text,
                    "started_at": seg.start_time,
                    "ended_at": seg.end_time,
                })
                
        return jsonify(result), HTTPStatus.OK
        
    except Exception as exc:
        return jsonify({"error": "internal_error", "details": str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR


@zoom_api.route("/sessions/<session_id>/analytics", methods=["GET"])
def get_session_analytics(session_id: str):
    """Get talk-time and interruption metrics per participant."""
    try:
        from models import SessionLocal
        from models.entities import MeetingAnalytics, ZoomMeeting
        
        with SessionLocal() as db_session:
            # Get zoom meeting for this session
            zoom_meeting = db_session.query(ZoomMeeting).filter_by(session_id=session_id).first()
            if not zoom_meeting:
                return jsonify({"error": "not_found", "details": "No Zoom meeting found for this session"}), HTTPStatus.NOT_FOUND
                
            # Get analytics
            analytics = db_session.query(MeetingAnalytics).filter_by(meeting_id=zoom_meeting.id).first()
            if not analytics:
                return jsonify([]), HTTPStatus.OK
                
            # Convert talk time distribution to per-participant format
            result = []
            if analytics.talk_time_distribution:
                for participant_id, talk_time_ms in analytics.talk_time_distribution.items():
                    result.append({
                        "participant_id": participant_id,
                        "talk_time_ms": talk_time_ms,
                        "interruptions": analytics.interruption_count or 0,  # Simplified
                    })
                    
        return jsonify(result), HTTPStatus.OK
        
    except Exception as exc:
        return jsonify({"error": "internal_error", "details": str(exc)}), HTTPStatus.INTERNAL_SERVER_ERROR