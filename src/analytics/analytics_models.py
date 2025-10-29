"""SQLAlchemy models for analytics metrics storage."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Boolean, Text,
    JSON, UniqueConstraint, Index, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


class AnalyticsMetric(Base):
    """Time-series storage for analytics metrics."""
    
    __tablename__ = "analytics_metrics"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    service_name = Column(String(100), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    session_id = Column(String(36), nullable=False)
    participant_id = Column(String(36), nullable=True)
    tags = Column(JSON, default={})
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    
    __table_args__ = (
        Index("idx_metrics_session_timestamp", "session_id", "timestamp"),
        Index("idx_metrics_participant_timestamp", "participant_id", "timestamp"),
        Index("idx_metrics_service_metric", "service_name", "metric_name"),
        Index("idx_metrics_timestamp", "timestamp"),
    )
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "service_name": self.service_name,
            "metric_name": self.metric_name,
            "value": self.metric_value,
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "tags": self.tags,
            "timestamp": self.timestamp.isoformat(),
        }


class AnalyticsAggregate(Base):
    """Pre-computed aggregate metrics."""
    
    __tablename__ = "analytics_aggregates"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), nullable=False)
    participant_id = Column(String(36), nullable=True)
    metric_name = Column(String(100), nullable=False)
    aggregation_type = Column(String(50), nullable=False)  # sum, avg, min, max, count
    time_window = Column(String(20), nullable=False)  # 1min, 5min, 1hour, session
    value = Column(Float, nullable=False)
    sample_count = Column(Integer, nullable=False, default=1)
    metadata = Column(JSON, default={})
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "participant_id",
            "metric_name",
            "aggregation_type",
            "time_window",
            "window_start",
            name="unique_aggregate"
        ),
        Index("idx_aggregates_session_window", "session_id", "window_start"),
        Index("idx_aggregates_metric_type", "metric_name", "aggregation_type"),
    )


class AnalyticsSessionSummary(Base):
    """Computed analytics summary per session."""
    
    __tablename__ = "analytics_session_summary"
    
    session_id = Column(String(36), primary_key=True)
    total_duration_seconds = Column(Float)
    participant_count = Column(Integer)
    total_talk_time_seconds = Column(Float)
    talk_time_distribution = Column(JSON)  # {"participant_id": seconds}
    participation_equality = Column(Float)  # 0-1 score
    total_words_spoken = Column(Integer)
    interruption_count = Column(Integer)
    average_speech_pace = Column(Float)  # words per minute
    engagement_score = Column(Float)  # 0-100
    metadata = Column(JSON, default={})
    computed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, 
                        default=datetime.now(timezone.utc),
                        onupdate=datetime.now(timezone.utc))
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "total_duration_seconds": self.total_duration_seconds,
            "participant_count": self.participant_count,
            "total_talk_time_seconds": self.total_talk_time_seconds,
            "talk_time_distribution": self.talk_time_distribution,
            "participation_equality": self.participation_equality,
            "total_words_spoken": self.total_words_spoken,
            "interruption_count": self.interruption_count,
            "average_speech_pace": self.average_speech_pace,
            "engagement_score": self.engagement_score,
            "metadata": self.metadata,
            "computed_at": self.computed_at.isoformat() if self.computed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AnalyticsRealtimeSnapshot(Base):
    """Real-time metric snapshots for dashboards."""
    
    __tablename__ = "analytics_realtime_snapshots"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), nullable=False)
    participant_id = Column(String(36), nullable=True)
    metrics = Column(JSON, nullable=False)  # {"talk_time": 120, "words": 500, ...}
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    ttl = Column(DateTime(timezone=True), nullable=False,
                 default=lambda: datetime.now(timezone.utc) + timedelta(hours=1))
    
    __table_args__ = (
        UniqueConstraint("session_id", "participant_id", name="unique_snapshot"),
        Index("idx_snapshots_session", "session_id"),
        Index("idx_snapshots_ttl", "ttl"),
    )


class AnalyticsEventsLog(Base):
    """Log of processed events for debugging."""
    
    __tablename__ = "analytics_events_log"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    event_id = Column(String(100), nullable=False)
    event_type = Column(String(50), nullable=False)
    session_id = Column(String(36), nullable=False)
    service_name = Column(String(100), nullable=False)
    processing_time_ms = Column(Integer)
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    
    __table_args__ = (
        Index("idx_events_session_created", "session_id", "created_at"),
        Index("idx_events_service", "service_name", "created_at"),
    )


# Helper functions for working with metrics

from datetime import timedelta
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import and_, func as sql_func


def store_metric(
    db: DBSession,
    service_name: str,
    metric_name: str,
    value: float,
    session_id: str,
    participant_id: Optional[str] = None,
    tags: Optional[dict] = None,
    timestamp: Optional[datetime] = None,
) -> AnalyticsMetric:
    """Store a metric in the database."""
    metric = AnalyticsMetric(
        service_name=service_name,
        metric_name=metric_name,
        metric_value=value,
        session_id=session_id,
        participant_id=participant_id,
        tags=tags or {},
        timestamp=timestamp or datetime.now(timezone.utc),
    )
    db.add(metric)
    db.commit()
    return metric


def get_latest_metric(
    db: DBSession,
    metric_name: str,
    session_id: str,
    participant_id: Optional[str] = None,
) -> Optional[AnalyticsMetric]:
    """Get the latest value for a metric."""
    query = db.query(AnalyticsMetric).filter(
        and_(
            AnalyticsMetric.metric_name == metric_name,
            AnalyticsMetric.session_id == session_id,
        )
    )
    
    if participant_id:
        query = query.filter(AnalyticsMetric.participant_id == participant_id)
    else:
        query = query.filter(AnalyticsMetric.participant_id.is_(None))
    
    return query.order_by(AnalyticsMetric.timestamp.desc()).first()


def compute_aggregate(
    db: DBSession,
    session_id: str,
    metric_name: str,
    aggregation_type: str,  # sum, avg, min, max, count
    time_window: str,  # 1min, 5min, 1hour
    participant_id: Optional[str] = None,
) -> float:
    """Compute aggregate metric for a time window."""
    # Parse time window
    window_map = {
        "1min": timedelta(minutes=1),
        "5min": timedelta(minutes=5),
        "1hour": timedelta(hours=1),
    }
    delta = window_map.get(time_window, timedelta(minutes=5))
    
    # Build query
    window_start = datetime.now(timezone.utc) - delta
    query = db.query(AnalyticsMetric).filter(
        and_(
            AnalyticsMetric.session_id == session_id,
            AnalyticsMetric.metric_name == metric_name,
            AnalyticsMetric.timestamp >= window_start,
        )
    )
    
    if participant_id:
        query = query.filter(AnalyticsMetric.participant_id == participant_id)
    
    # Apply aggregation
    if aggregation_type == "sum":
        result = db.query(sql_func.sum(AnalyticsMetric.metric_value)).filter(
            query.whereclause
        ).scalar()
    elif aggregation_type == "avg":
        result = db.query(sql_func.avg(AnalyticsMetric.metric_value)).filter(
            query.whereclause
        ).scalar()
    elif aggregation_type == "min":
        result = db.query(sql_func.min(AnalyticsMetric.metric_value)).filter(
            query.whereclause
        ).scalar()
    elif aggregation_type == "max":
        result = db.query(sql_func.max(AnalyticsMetric.metric_value)).filter(
            query.whereclause
        ).scalar()
    elif aggregation_type == "count":
        result = query.count()
    else:
        raise ValueError(f"Unknown aggregation type: {aggregation_type}")
    
    return float(result) if result is not None else 0.0