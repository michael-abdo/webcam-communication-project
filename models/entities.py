"""ORM entities for session, participant, and media chunk records."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    CHAR,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
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
    device_kind: Mapped[str] = mapped_column(String(100), nullable=False)
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
