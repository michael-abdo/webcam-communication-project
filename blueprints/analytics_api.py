"""API endpoints for meeting analytics."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Dict, Any, Optional, List

from flask import Blueprint, jsonify, request
import redis
from sqlalchemy import text

from config import get_capture_api_token
from models import SessionLocal
from models.entities import ZoomMeeting, MeetingAnalytics
from services.capture_service import (
    CaptureNotFoundError,
    create_meeting_analytics,
    get_meeting_analytics,
)

analytics_api = Blueprint("analytics_api", __name__, url_prefix="/api/analytics")
logger = logging.getLogger(__name__)

# Redis connection for real-time metrics
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_client = None

try:
    # Handle Heroku Redis SSL requirements
    if REDIS_URL.startswith('rediss://'):
        import ssl
        redis_client = redis.from_url(
            REDIS_URL, 
            decode_responses=True,
            ssl_cert_reqs=ssl.CERT_NONE
        )
    else:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
except Exception as e:
    logger.warning(f"Redis not available for real-time analytics: {e}")


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


@analytics_api.route("/sessions/<session_id>/talk-time", methods=["GET"])
def get_session_talk_time(session_id: str):
    """
    Get talk time analytics for a specific session.
    
    Returns real-time talk time distribution and participation metrics.
    """
    try:
        # First, try to get real-time data from Redis
        talk_time_data = _get_realtime_talk_time(session_id)
        
        if talk_time_data:
            return jsonify(talk_time_data), HTTPStatus.OK
        
        # Fallback to database - check if we have analytics data
        with SessionLocal() as session:
            # Try to find meeting analytics by session_id
            analytics = session.query(MeetingAnalytics).filter(
                MeetingAnalytics.session_id == session_id
            ).first()
            
            if analytics and analytics.talk_time_distribution:
                return jsonify(_format_talk_time_response(analytics)), HTTPStatus.OK
            
            # No data found
            return jsonify({
                "session_id": session_id,
                "error": "No analytics data found for this session",
                "participant_count": 0,
                "talk_time_distribution": {}
            }), HTTPStatus.NOT_FOUND
            
    except Exception as e:
        logger.error(f"Error fetching talk time for session {session_id}: {e}")
        return jsonify({"error": "Internal server error"}), HTTPStatus.INTERNAL_SERVER_ERROR


@analytics_api.route("/meetings/<meeting_id>/talk-time", methods=["GET"])
def get_meeting_talk_time(meeting_id: str):
    """
    Get aggregated talk time analytics for a meeting.
    """
    try:
        with SessionLocal() as session:
            # Get meeting with analytics
            meeting = session.query(ZoomMeeting).filter(
                ZoomMeeting.meeting_uuid == meeting_id
            ).first()
            
            if not meeting or not meeting.analytics:
                return jsonify({
                    "meeting_id": meeting_id,
                    "error": "No analytics data found for this meeting"
                }), HTTPStatus.NOT_FOUND
            
            analytics = meeting.analytics
            if not analytics.talk_time_distribution:
                return jsonify({
                    "meeting_id": meeting_id,
                    "session_id": analytics.session_id,
                    "participant_count": analytics.participant_count,
                    "talk_time_distribution": {},
                    "message": "No talk time data available"
                }), HTTPStatus.OK
            
            return jsonify(_format_talk_time_response(analytics)), HTTPStatus.OK
            
    except Exception as e:
        logger.error(f"Error fetching talk time for meeting {meeting_id}: {e}")
        return jsonify({"error": "Internal server error"}), HTTPStatus.INTERNAL_SERVER_ERROR


def _get_realtime_talk_time(session_id: str) -> Optional[Dict[str, Any]]:
    """Get real-time talk time data from Redis cache."""
    if not redis_client:
        return None
    
    try:
        # Get all talk time counters for the session
        talk_times = {}
        word_counts = {}
        participant_names = {}
        
        # Scan for talk time metrics
        pattern = f"metrics:talk_time_seconds:{session_id}:*"
        for key in redis_client.scan_iter(match=pattern):
            participant_id = key.split(':')[-1]
            value = redis_client.get(key)
            if value:
                talk_times[participant_id] = float(value)
        
        if not talk_times:
            return None
        
        # Get word counts
        pattern = f"metrics:words_spoken:{session_id}:*"
        for key in redis_client.scan_iter(match=pattern):
            participant_id = key.split(':')[-1]
            value = redis_client.get(key)
            if value:
                word_counts[participant_id] = int(value)
        
        # Get participant names from cache
        pattern = f"participant:{session_id}:*:name"
        for key in redis_client.scan_iter(match=pattern):
            parts = key.split(':')
            participant_id = parts[2]
            name = redis_client.get(key)
            if name:
                participant_names[participant_id] = name
        
        # Calculate totals and percentages
        total_talk_time = sum(talk_times.values())
        talk_time_distribution = {}
        
        for participant_id, talk_time in talk_times.items():
            percentage = (talk_time / total_talk_time * 100) if total_talk_time > 0 else 0
            talk_time_distribution[participant_id] = {
                "id": participant_id,
                "name": participant_names.get(participant_id, f"Participant {participant_id[:8]}"),
                "talk_time_seconds": talk_time,
                "percentage": round(percentage, 2),
                "words_spoken": word_counts.get(participant_id, 0)
            }
        
        # Calculate participation equality
        equality = _calculate_participation_equality(list(talk_times.values()))
        
        return {
            "session_id": session_id,
            "total_talk_time_seconds": total_talk_time,
            "participant_count": len(talk_times),
            "talk_time_distribution": talk_time_distribution,
            "participation_equality": round(equality, 2),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "data_source": "realtime"
        }
        
    except Exception as e:
        logger.error(f"Error getting realtime talk time: {e}")
        return None


def _format_talk_time_response(analytics: MeetingAnalytics) -> Dict[str, Any]:
    """Format analytics object into talk time API response."""
    talk_time_dist = analytics.talk_time_distribution or {}
    
    # Calculate total talk time
    total_talk_time = sum(
        data.get('duration', 0) if isinstance(data, dict) else 0
        for data in talk_time_dist.values()
    )
    
    # Format distribution with percentages
    formatted_dist = {}
    for participant_id, data in talk_time_dist.items():
        if isinstance(data, dict):
            duration = data.get('duration', 0)
            percentage = (duration / total_talk_time * 100) if total_talk_time > 0 else 0
            formatted_dist[participant_id] = {
                "id": participant_id,
                "name": data.get('name', f'Participant {participant_id[:8]}'),
                "talk_time_seconds": duration,
                "percentage": round(percentage, 2)
            }
    
    # Calculate participation equality
    values = [d['talk_time_seconds'] for d in formatted_dist.values()]
    equality = _calculate_participation_equality(values) if values else 0
    
    return {
        "session_id": analytics.session_id,
        "meeting_id": analytics.meeting_uuid,
        "total_duration_seconds": analytics.duration,
        "total_talk_time_seconds": total_talk_time,
        "participant_count": analytics.participant_count or len(formatted_dist),
        "talk_time_distribution": formatted_dist,
        "participation_equality": round(equality, 2),
        "last_updated": analytics.updated_at.isoformat() if analytics.updated_at else None,
        "data_source": "database"
    }


def _calculate_participation_equality(values: List[float]) -> float:
    """
    Calculate participation equality score (0-1).
    Uses inverted Gini coefficient where 1 = perfect equality.
    """
    if not values or len(values) < 2:
        return 1.0
    
    # Remove zeros
    values = [v for v in values if v > 0]
    if not values:
        return 1.0
    
    # Sort values
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    # Calculate Gini coefficient
    cumsum = 0
    for i, value in enumerate(sorted_values):
        cumsum += value * (n - i)
    
    total = sum(sorted_values)
    if total == 0:
        return 1.0
    
    gini = (n + 1 - 2 * cumsum / total) / n
    
    # Return equality (inverse of Gini)
    return max(0, min(1, 1 - gini))