# Database Schema Implementation Plan

## Overview
This document outlines the plan to add 5 missing database tables required for Phase 2 Zoom integration. The implementation follows existing patterns in the codebase and maintains consistency with current architecture.

## Current Database Architecture

### Existing Tables
- **sessions** - Core capture session records
- **participants** - Device-based participant tracking
- **media_chunks** - Stored audio/video chunk metadata
- **session_transcripts** - Session transcript metadata
- **session_logs** - Session event logs

### Technology Stack
- SQLAlchemy ORM with declarative models
- PostgreSQL/SQLite support
- Auto-table creation via `init_engine()`
- UUID primary keys
- Timezone-aware timestamps

## Database Schema Diagram

```mermaid
erDiagram
    sessions ||--o| zoom_meetings : "has one"
    sessions ||--o{ transcription_segments : "has many"
    sessions ||--o{ media_chunks : "has many"
    sessions ||--o{ participants : "has many"
    sessions ||--o| session_transcripts : "has one"
    sessions ||--o{ session_logs : "has many"
    
    zoom_meetings ||--o{ zoom_participants : "has many"
    zoom_meetings ||--o| meeting_analytics : "has one"
    zoom_meetings ||--o{ rtms_health_status : "has many"
    
    participants ||--o{ media_chunks : "has many"
    participants ||--o{ transcription_segments : "may have"
    
    sessions {
        uuid id PK
        string facilitator_id
        timestamp consent_at
        string device_kind
        string locale
    }
    
    zoom_meetings {
        uuid id PK
        string meeting_uuid UK
        uuid session_id FK_UK
        string topic
        string host_id
        timestamp start_time
        timestamp end_time
        string rtms_stream_id
        string recording_status
    }
    
    zoom_participants {
        uuid id PK
        uuid meeting_id FK
        string zoom_user_id
        string display_name
        string email
        timestamp join_time
        timestamp leave_time
        string role
    }
    
    transcription_segments {
        uuid id PK
        uuid session_id FK
        uuid participant_id FK
        text text
        float start_time
        float end_time
        float confidence
        string language
    }
    
    meeting_analytics {
        uuid id PK
        uuid meeting_id FK_UK
        int total_duration_seconds
        int participant_count
        json talk_time_distribution
        int interruption_count
        float avg_speech_pace
        timestamp computed_at
    }
    
    rtms_health_status {
        uuid id PK
        uuid meeting_id FK
        string stream_id
        string status
        int latency_ms
        int frames_processed
        json errors
        timestamp checked_at
    }
```

## New Tables to Implement

### 1. zoom_meetings
**Purpose**: Store Zoom meeting metadata and link to capture sessions

**Schema**:
```sql
CREATE TABLE zoom_meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_uuid VARCHAR(255) UNIQUE NOT NULL,
    session_id UUID UNIQUE REFERENCES sessions(id),
    topic VARCHAR(500),
    host_id VARCHAR(255) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    rtms_stream_id VARCHAR(255),
    recording_status VARCHAR(50) DEFAULT 'none',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_zoom_meetings_start_time ON zoom_meetings(start_time);
```

**Relationships**:
- One-to-One with sessions table
- One-to-Many with zoom_participants
- One-to-One with meeting_analytics
- One-to-Many with rtms_health_status

### 2. zoom_participants
**Purpose**: Track Zoom-specific participant information

**Schema**:
```sql
CREATE TABLE zoom_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES zoom_meetings(id) ON DELETE CASCADE,
    zoom_user_id VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    email VARCHAR(255),
    join_time TIMESTAMP WITH TIME ZONE NOT NULL,
    leave_time TIMESTAMP WITH TIME ZONE,
    role VARCHAR(50) DEFAULT 'participant',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_zoom_participants_meeting_user ON zoom_participants(meeting_id, zoom_user_id);
CREATE INDEX idx_zoom_participants_join_time ON zoom_participants(join_time);
```

### 3. transcription_segments
**Purpose**: Store speaker-attributed transcription segments

**Schema**:
```sql
CREATE TABLE transcription_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    participant_id UUID REFERENCES participants(id) ON DELETE SET NULL,
    text TEXT NOT NULL,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    confidence FLOAT,
    language VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transcription_segments_session_time ON transcription_segments(session_id, start_time);
CREATE INDEX idx_transcription_segments_participant ON transcription_segments(participant_id);
```

### 4. meeting_analytics
**Purpose**: Store computed analytics for each meeting

**Schema**:
```sql
CREATE TABLE meeting_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID UNIQUE NOT NULL REFERENCES zoom_meetings(id) ON DELETE CASCADE,
    total_duration_seconds INTEGER NOT NULL,
    participant_count INTEGER NOT NULL,
    talk_time_distribution JSONB,
    interruption_count INTEGER DEFAULT 0,
    avg_speech_pace FLOAT,
    computed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_meeting_analytics_computed_at ON meeting_analytics(computed_at);
```

### 5. rtms_health_status
**Purpose**: Monitor RTMS stream health and connection status

**Schema**:
```sql
CREATE TABLE rtms_health_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID NOT NULL REFERENCES zoom_meetings(id) ON DELETE CASCADE,
    stream_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    latency_ms INTEGER,
    frames_processed INTEGER DEFAULT 0,
    errors JSONB,
    checked_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rtms_health_meeting_time ON rtms_health_status(meeting_id, checked_at);
CREATE INDEX idx_rtms_health_stream_status ON rtms_health_status(stream_id, status);
```

## SQLAlchemy Models

### Location: `models/entities.py`

```python
class ZoomMeeting(Base):
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
    recording_status: Mapped[str] = mapped_column(String(50), default="none")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="zoom_meeting")
    zoom_participants: Mapped[list["ZoomParticipant"]] = relationship(
        "ZoomParticipant", back_populates="meeting", cascade="all, delete-orphan"
    )
    analytics: Mapped["MeetingAnalytics | None"] = relationship(
        "MeetingAnalytics", back_populates="meeting", uselist=False
    )
    health_checks: Mapped[list["RTMSHealthStatus"]] = relationship(
        "RTMSHealthStatus", back_populates="meeting", cascade="all, delete-orphan"
    )
```

## Service Functions

### Location: `services/capture_service.py`

1. **create_zoom_meeting(meeting_uuid, session_id, host_id, topic, start_time)**
2. **get_zoom_meeting(meeting_id)**
3. **create_zoom_participant(meeting_id, zoom_user_id, display_name, email, role)**
4. **create_transcription_segment(session_id, text, start_time, end_time, participant_id)**
5. **create_meeting_analytics(meeting_id, analytics_data)**
6. **record_rtms_health_check(meeting_id, stream_id, status, metrics)**

## API Endpoints

### 1. Meeting Management
- `POST /api/meetings` - Create new Zoom meeting record
- `GET /api/meetings/{meeting_id}` - Get meeting details
- `GET /api/meetings` - List meetings with filtering

### 2. Participant Management
- `POST /api/meetings/{meeting_id}/participants` - Add participant
- `GET /api/meetings/{meeting_id}/participants` - List participants

### 3. Transcription Access
- `POST /api/transcription/segments` - Add transcription segment
- `GET /api/sessions/{session_id}/transcription` - Get full transcription

### 4. Analytics Retrieval
- `GET /api/analytics/meetings/{meeting_id}` - Get meeting analytics
- `POST /api/analytics/compute/{meeting_id}` - Trigger analytics computation

### 5. Health Monitoring
- `POST /api/rtms/health` - Record health check
- `GET /api/rtms/health/{stream_id}` - Get health status

## Implementation Steps

### Phase 1: Database Models (Day 1)
1. Add all 5 model classes to `models/entities.py`
2. Update `models/__init__.py` to export new models
3. Test table creation with `init_engine()`
4. Verify relationships and constraints

### Phase 2: Service Layer (Day 2)
1. Add service functions to `capture_service.py`
2. Implement error handling (NotFound, Conflict)
3. Add unit tests for service functions

### Phase 3: API Development (Day 3-4)
1. Create `blueprints/meetings_api.py`
2. Create `blueprints/analytics_api.py`
3. Update `rtms_ingest_api.py` for meeting creation
4. Register blueprints in `app_lightweight.py`

### Phase 4: Integration (Day 5)
1. Update RTMS webhook handler to create zoom_meetings
2. Modify session creation to link with meetings
3. Test end-to-end flow with RTMS

## Dependencies and Risks

### Dependencies
- Existing Session and Participant tables
- RTMS webhook data structure
- S3 storage for media chunks

### Risks
1. **Data Migration**: Existing sessions won't have zoom_meeting records
2. **Performance**: Analytics computation may be CPU-intensive
3. **Storage**: Transcription segments could grow large

### Mitigation
1. Make zoom_meeting association optional initially
2. Implement async analytics computation
3. Add pagination for transcription queries

## Success Metrics
- All tables created successfully
- RTMS webhooks create meeting records
- API endpoints return expected data
- No performance degradation

## Next Steps
1. Review this plan with team
2. Create feature branch `feature/phase-2-database`
3. Implement models incrementally
4. Deploy to staging for testing

---

**Estimated Timeline**: 5 days
**Effort**: 1 developer
**Priority**: High (blocks other Phase 2 features)