"""ORM entities for session, participant, and media chunk records."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    CHAR,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Session(Base):
    """Capture session for a facilitator."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=_uuid,
    )
    facilitator_id: Mapped[str] = mapped_column(String(255), nullable=False)
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    device_kind: Mapped[str] = mapped_column(String(255), nullable=False)
    locale: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    participants: Mapped[list["Participant"]] = relationship(
        "Participant",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    media_chunks: Mapped[list["MediaChunk"]] = relationship(
        "MediaChunk",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="MediaChunk.sequence_no",
    )
    transcript: Mapped["SessionTranscript | None"] = relationship(
        "SessionTranscript",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )
    logs: Mapped[list["SessionLog"]] = relationship(
        "SessionLog",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionLog.recorded_at.desc()",
    )
    zoom_meeting: Mapped["ZoomMeeting | None"] = relationship(
        "ZoomMeeting",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )
    transcription_segments: Mapped[list["TranscriptionSegment"]] = relationship(
        "TranscriptionSegment",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="TranscriptionSegment.start_time",
    )
    events: Mapped[list["SessionEvent"]] = relationship(
        "SessionEvent",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionEvent.occurred_at",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "facilitator_id": self.facilitator_id,
            "consent_at": self.consent_at.isoformat(),
            "device_kind": self.device_kind,
            "locale": self.locale,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "participants": [participant.to_dict() for participant in self.participants],
            "chunks": [chunk.to_dict() for chunk in self.media_chunks],
            "transcript": self.transcript.to_dict() if self.transcript else None,
            "logs": [log.to_dict() for log in self.logs],
        }


class Participant(Base):
    """Device participant metadata for a session."""

    __tablename__ = "participants"

    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=_uuid,
    )
    session_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    device_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    session: Mapped["Session"] = relationship("Session", back_populates="participants")
    media_chunks: Mapped[list["MediaChunk"]] = relationship(
        "MediaChunk",
        back_populates="participant",
    )
    transcription_segments: Mapped[list["TranscriptionSegment"]] = relationship(
        "TranscriptionSegment",
        back_populates="participant",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "device_id": self.device_id,
            "status": self.status,
            "last_heartbeat_at": self.last_heartbeat_at.isoformat()
            if self.last_heartbeat_at
            else None,
            "created_at": self.created_at.isoformat(),
        }


class MediaChunk(Base):
    """Stored media chunk metadata."""

    __tablename__ = "media_chunks"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence_no", name="uq_chunk_seq"),
    )

    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=_uuid,
    )
    session_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    participant_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("participants.id", ondelete="SET NULL"), nullable=True
    )
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    session: Mapped["Session"] = relationship("Session", back_populates="media_chunks")
    participant: Mapped["Participant | None"] = relationship(
        "Participant", back_populates="media_chunks"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "sequence_no": self.sequence_no,
            "checksum": self.checksum,
            "duration_ms": self.duration_ms,
            "storage_key": self.storage_key,
            "stored_at": self.stored_at.isoformat(),
            "created_at": self.created_at.isoformat(),
        }


class SessionTranscript(Base):
    """Session transcript artifact metadata."""

    __tablename__ = "session_transcripts"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("sessions.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)

    session: Mapped["Session"] = relationship("Session", back_populates="transcript")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "storage_key": self.storage_key,
            "status": self.status,
            "mime_type": self.mime_type,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "source": self.source,
        }


class SessionLog(Base):
    """Session log artifact metadata."""

    __tablename__ = "session_logs"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    log_type: Mapped[str] = mapped_column(String(100), nullable=False, default="capture")
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped["Session"] = relationship("Session", back_populates="logs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "log_type": self.log_type,
            "storage_key": self.storage_key,
            "status": self.status,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }


class ZoomMeeting(Base):
    """Zoom meeting metadata and link to capture sessions."""

    __tablename__ = "zoom_meetings"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    meeting_uuid: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    session_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("sessions.id"), unique=True, nullable=False
    )
    topic: Mapped[str | None] = mapped_column(String(500), nullable=True)
    host_id: Mapped[str] = mapped_column(String(255), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rtms_stream_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recording_status: Mapped[str] = mapped_column(String(50), nullable=False, default="none")
    vault_credential_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    capture_worker_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    capture_status: Mapped[str] = mapped_column(String(50), nullable=False, default="idle")
    capture_last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="zoom_meeting")
    zoom_participants: Mapped[list["ZoomParticipant"]] = relationship(
        "ZoomParticipant",
        back_populates="meeting",
        cascade="all, delete-orphan",
    )
    analytics: Mapped["MeetingAnalytics | None"] = relationship(
        "MeetingAnalytics",
        back_populates="meeting",
        uselist=False,
        cascade="all, delete-orphan",
    )
    health_checks: Mapped[list["RTMSHealthStatus"]] = relationship(
        "RTMSHealthStatus",
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="RTMSHealthStatus.checked_at.desc()",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "meeting_uuid": self.meeting_uuid,
            "session_id": self.session_id,
            "topic": self.topic,
            "host_id": self.host_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "rtms_stream_id": self.rtms_stream_id,
            "recording_status": self.recording_status,
            "vault_credential_ref": self.vault_credential_ref,
            "capture_worker_id": self.capture_worker_id,
            "capture_status": self.capture_status,
            "capture_last_heartbeat": self.capture_last_heartbeat.isoformat() if self.capture_last_heartbeat else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "participants": [p.to_dict() for p in self.zoom_participants],
            "analytics": self.analytics.to_dict() if self.analytics else None,
            "health_checks": [h.to_dict() for h in self.health_checks],
        }


class ZoomParticipant(Base):
    """Zoom-specific participant information."""

    __tablename__ = "zoom_participants"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    meeting_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("zoom_meetings.id", ondelete="CASCADE"), nullable=False
    )
    zoom_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    join_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    leave_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="participant")
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    meeting: Mapped["ZoomMeeting"] = relationship("ZoomMeeting", back_populates="zoom_participants")
    events: Mapped[list["SessionEvent"]] = relationship("SessionEvent", back_populates="participant")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "meeting_id": self.meeting_id,
            "zoom_user_id": self.zoom_user_id,
            "display_name": self.display_name,
            "email": self.email,
            "join_time": self.join_time.isoformat(),
            "leave_time": self.leave_time.isoformat() if self.leave_time else None,
            "role": self.role,
            "consent_at": self.consent_at.isoformat() if self.consent_at else None,
            "created_at": self.created_at.isoformat(),
        }


class TranscriptionSegment(Base):
    """Speaker-attributed transcription segments."""

    __tablename__ = "transcription_segments"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    participant_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("participants.id", ondelete="SET NULL"), nullable=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="transcription_segments")
    participant: Mapped["Participant | None"] = relationship(
        "Participant", back_populates="transcription_segments"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "confidence": self.confidence,
            "language": self.language,
            "created_at": self.created_at.isoformat(),
        }


class MeetingAnalytics(Base):
    """Computed analytics for each meeting."""

    __tablename__ = "meeting_analytics"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    meeting_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("zoom_meetings.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    total_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    participant_count: Mapped[int] = mapped_column(Integer, nullable=False)
    talk_time_distribution: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    interruption_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_speech_pace: Mapped[float | None] = mapped_column(Float, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    meeting: Mapped["ZoomMeeting"] = relationship("ZoomMeeting", back_populates="analytics")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "meeting_id": self.meeting_id,
            "total_duration_seconds": self.total_duration_seconds,
            "participant_count": self.participant_count,
            "talk_time_distribution": self.talk_time_distribution,
            "interruption_count": self.interruption_count,
            "avg_speech_pace": self.avg_speech_pace,
            "computed_at": self.computed_at.isoformat(),
            "created_at": self.created_at.isoformat(),
        }


class SessionEvent(Base):
    """Track session lifecycle events (join, leave, flag)."""

    __tablename__ = "session_events"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    participant_id: Mapped[str | None] = mapped_column(
        CHAR(36), ForeignKey("zoom_participants.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="events")
    participant: Mapped["ZoomParticipant | None"] = relationship("ZoomParticipant", back_populates="events")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "occurred_at": self.occurred_at.isoformat(),
            "created_at": self.created_at.isoformat(),
        }


class RTMSHealthStatus(Base):
    """RTMS stream health and connection status monitoring."""

    __tablename__ = "rtms_health_status"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    meeting_id: Mapped[str] = mapped_column(
        CHAR(36), ForeignKey("zoom_meetings.id", ondelete="CASCADE"), nullable=False
    )
    stream_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frames_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    meeting: Mapped["ZoomMeeting"] = relationship("ZoomMeeting", back_populates="health_checks")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "meeting_id": self.meeting_id,
            "stream_id": self.stream_id,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "frames_processed": self.frames_processed,
            "errors": self.errors,
            "checked_at": self.checked_at.isoformat(),
            "created_at": self.created_at.isoformat(),
        }
