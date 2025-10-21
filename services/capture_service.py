"""Capture persistence service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session as SASession

from models import SessionLocal
from models.database import db_session
from models.entities import MediaChunk, Participant, Session


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
