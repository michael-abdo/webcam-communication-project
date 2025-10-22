"""Capture persistence service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from models import SessionLocal
from models.database import db_session
from models.entities import MediaChunk, Participant, Session, SessionLog, SessionTranscript


class CaptureNotFoundError(Exception):
    """Raised when a requested capture record cannot be found."""


class CaptureConflictError(Exception):
    """Raised when capture data violates sequencing or uniqueness rules."""


def _utc_datetime(value: datetime) -> datetime:
    """Ensure datetime has tzinfo (assume UTC if naive)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def create_session_record(
    facilitator_id: str,
    consent_at: datetime,
    device_kind: str,
    locale: Optional[str] = None,
) -> dict:
    consent_ts = _utc_datetime(consent_at)

    with db_session() as session:
        capture = Session(
            facilitator_id=facilitator_id,
            consent_at=consent_ts,
            device_kind=device_kind,
            locale=locale,
        )
        session.add(capture)
        session.flush()
        session.refresh(capture)
        data = capture.to_dict()
        return data


def get_session_record(session_id: str) -> dict:
    with SessionLocal() as session:
        capture = session.get(Session, session_id)
        if capture is None:
            raise CaptureNotFoundError(f"Session {session_id} not found")
        # Eagerly load relationships to avoid lazy-load after close
        capture.participants  # noqa: B018
        capture.media_chunks  # noqa: B018
        if capture.transcript:
            capture.transcript
        capture.logs  # noqa: B018
        data = capture.to_dict()
        return data


def create_participant_record(
    session_id: str,
    device_id: str,
    status: str,
    last_heartbeat_at: Optional[datetime] = None,
) -> dict:
    heartbeat = _utc_datetime(last_heartbeat_at) if last_heartbeat_at else None

    with db_session() as session:
        capture = session.get(Session, session_id)
        if capture is None:
            raise CaptureNotFoundError(f"Session {session_id} not found")

        participant = Participant(
            session_id=session_id,
            device_id=device_id,
            status=status,
            last_heartbeat_at=heartbeat,
        )
        session.add(participant)
        session.flush()
        session.refresh(participant)
        return participant.to_dict()


def record_media_chunk(
    session_id: str,
    sequence_no: int,
    checksum: str,
    duration_ms: int,
    storage_key: str,
    participant_id: Optional[str] = None,
    stored_at: Optional[datetime] = None,
) -> dict:
    stored_ts = _utc_datetime(stored_at) if stored_at else datetime.now(timezone.utc)

    with db_session() as session:
        capture = session.get(Session, session_id)
        if capture is None:
            raise CaptureNotFoundError(f"Session {session_id} not found")

        if participant_id:
            participant = session.get(Participant, participant_id)
            if participant is None or participant.session_id != session_id:
                raise CaptureNotFoundError(
                    f"Participant {participant_id} not found for session {session_id}"
                )

        chunk = MediaChunk(
            session_id=session_id,
            participant_id=participant_id,
            sequence_no=sequence_no,
            checksum=checksum,
            duration_ms=duration_ms,
            storage_key=storage_key,
            stored_at=stored_ts,
        )

        session.add(chunk)
        try:
            session.flush()
        except IntegrityError as exc:
            session.rollback()
            raise CaptureConflictError(
                f"Chunk sequence {sequence_no} already exists for session {session_id}"
            ) from exc

        session.refresh(chunk)
        return chunk.to_dict()


def list_session_chunks(session_id: str) -> list[dict]:
    with SessionLocal() as session:
        capture = session.get(Session, session_id)
        if capture is None:
            raise CaptureNotFoundError(f"Session {session_id} not found")
        capture.media_chunks  # Trigger load
        return [chunk.to_dict() for chunk in capture.media_chunks]


def list_recent_sessions(limit: int = 20) -> list[dict]:
    """Return recent sessions with participant/chunk counts for reviewers."""
    with SessionLocal() as session:
        captures = (
            session.query(Session)
            .options(
                selectinload(Session.participants),
                selectinload(Session.media_chunks),
                selectinload(Session.transcript),
                selectinload(Session.logs),
            )
            .order_by(Session.created_at.desc())
            .limit(limit)
            .all()
        )

    results: list[dict] = []
    for capture in captures:
        chunks = capture.media_chunks
        latest_chunk_at = None
        if chunks:
            latest_chunk = max(
                chunks,
                key=lambda c: c.stored_at or datetime.min.replace(tzinfo=timezone.utc),
            )
            latest_chunk_at = (
                latest_chunk.stored_at.isoformat() if latest_chunk.stored_at else None
            )

        transcript_status = "not_available"
        transcript_storage = None
        if capture.transcript:
            transcript_status = (capture.transcript.status or "unknown").lower()
            transcript_storage = capture.transcript.storage_key

        log_status = _aggregate_log_status(capture.logs)

        alert_state = "ok"
        if (
            not chunks
            or transcript_status in {"failed", "attention_required"}
            or log_status in {"failed", "attention_required"}
        ):
            alert_state = "attention_required"

        results.append(
            {
                "id": capture.id,
                "facilitator_id": capture.facilitator_id,
                "consent_at": capture.consent_at.isoformat(),
                "device_kind": capture.device_kind,
                "locale": capture.locale,
                "created_at": capture.created_at.isoformat(),
                "participant_count": len(capture.participants),
                "chunk_count": len(chunks),
                "latest_chunk_at": latest_chunk_at,
                "transcript_status": transcript_status,
                "log_status": log_status,
                "transcript_storage_key": transcript_storage,
                "alert_state": alert_state,
            }
        )

    return results


def _aggregate_log_status(logs: list[SessionLog]) -> str:
    if not logs:
        return "not_available"
    statuses = [log.status.lower() for log in logs if log.status]
    if any(status in {"failed", "error"} for status in statuses):
        return "failed"
    if any(status in {"attention_required", "processing", "pending"} for status in statuses):
        return "attention_required"
    if any(status == "completed" for status in statuses):
        return "completed"
    return statuses[0] if statuses else "unknown"


def upsert_transcript_record(
    session_id: str,
    status: str,
    storage_key: str | None = None,
    mime_type: str | None = None,
    generated_at: Optional[datetime] = None,
    source: str | None = None,
) -> dict:
    with db_session() as session:
        capture = session.get(Session, session_id)
        if capture is None:
            raise CaptureNotFoundError(f"Session {session_id} not found")

        transcript = (
            session.query(SessionTranscript)
            .filter_by(session_id=session_id)
            .one_or_none()
        )
        if transcript is None:
            transcript = SessionTranscript(session_id=session_id)
            session.add(transcript)

        transcript.status = status
        transcript.storage_key = storage_key or transcript.storage_key
        transcript.mime_type = mime_type or transcript.mime_type
        transcript.generated_at = _utc_datetime(generated_at) if generated_at else transcript.generated_at
        transcript.source = source or transcript.source
        session.flush()
        session.refresh(transcript)
        return transcript.to_dict()


def create_log_record(
    session_id: str,
    log_type: str,
    status: str,
    storage_key: str | None = None,
    message: str | None = None,
    recorded_at: Optional[datetime] = None,
) -> dict:
    with db_session() as session:
        capture = session.get(Session, session_id)
        if capture is None:
            raise CaptureNotFoundError(f"Session {session_id} not found")

        log_entry = SessionLog(
            session_id=session_id,
            log_type=log_type,
            status=status,
            storage_key=storage_key,
            message=message,
            recorded_at=_utc_datetime(recorded_at) if recorded_at else None,
        )
        session.add(log_entry)
        session.flush()
        session.refresh(log_entry)
        return log_entry.to_dict()


def list_session_logs(session_id: str) -> list[dict]:
    with SessionLocal() as session:
        capture = session.get(Session, session_id)
        if capture is None:
            raise CaptureNotFoundError(f"Session {session_id} not found")
        capture.logs  # trigger load
        return [log.to_dict() for log in capture.logs]
