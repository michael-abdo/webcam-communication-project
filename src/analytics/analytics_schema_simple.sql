-- Analytics Database Schema for Metrics Storage
-- Simplified version for Heroku PostgreSQL

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Analytics metrics table
CREATE TABLE IF NOT EXISTS analytics_metrics (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    session_id CHAR(36) NOT NULL,
    participant_id CHAR(36),
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_metrics_session_timestamp ON analytics_metrics (session_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_participant_timestamp ON analytics_metrics (participant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_service_metric ON analytics_metrics (service_name, metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON analytics_metrics (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_tags ON analytics_metrics USING GIN (tags);

-- Aggregated metrics table for pre-computed values
CREATE TABLE IF NOT EXISTS analytics_aggregates (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id CHAR(36) NOT NULL,
    participant_id CHAR(36),
    metric_name VARCHAR(100) NOT NULL,
    aggregation_type VARCHAR(50) NOT NULL, -- 'sum', 'avg', 'min', 'max', 'count'
    time_window VARCHAR(20) NOT NULL, -- '1min', '5min', '1hour', 'session'
    value DOUBLE PRECISION NOT NULL,
    sample_count INTEGER NOT NULL DEFAULT 1,
    metadata JSONB DEFAULT '{}',
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for analytics_aggregates
CREATE INDEX IF NOT EXISTS idx_aggregates_session_window ON analytics_aggregates (session_id, window_start DESC);
CREATE INDEX IF NOT EXISTS idx_aggregates_metric_type ON analytics_aggregates (metric_name, aggregation_type);
CREATE INDEX IF NOT EXISTS idx_aggregates_unique ON analytics_aggregates (session_id, participant_id, metric_name, aggregation_type, time_window, window_start);

-- Session analytics summary table
CREATE TABLE IF NOT EXISTS analytics_session_summary (
    session_id CHAR(36) PRIMARY KEY,
    total_duration_seconds DOUBLE PRECISION,
    participant_count INTEGER,
    total_talk_time_seconds DOUBLE PRECISION,
    talk_time_distribution JSONB, -- {"participant_id": seconds}
    participation_equality DOUBLE PRECISION, -- 0-1 score
    total_words_spoken INTEGER,
    interruption_count INTEGER,
    average_speech_pace DOUBLE PRECISION, -- words per minute
    engagement_score DOUBLE PRECISION, -- 0-100
    metadata JSONB DEFAULT '{}',
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Real-time metric snapshots for dashboards
CREATE TABLE IF NOT EXISTS analytics_realtime_snapshots (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id CHAR(36) NOT NULL,
    participant_id CHAR(36),
    metrics JSONB NOT NULL, -- {"talk_time": 120, "words": 500, ...}
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ttl TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '1 hour'
);

-- Create indexes for analytics_realtime_snapshots
CREATE INDEX IF NOT EXISTS idx_snapshots_session ON analytics_realtime_snapshots (session_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_ttl ON analytics_realtime_snapshots (ttl);
CREATE INDEX IF NOT EXISTS idx_snapshots_unique ON analytics_realtime_snapshots (session_id, participant_id);

-- Analytics events log for debugging
CREATE TABLE IF NOT EXISTS analytics_events_log (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    event_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    session_id CHAR(36) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    processing_time_ms INTEGER,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for analytics_events_log
CREATE INDEX IF NOT EXISTS idx_events_session_created ON analytics_events_log (session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_service ON analytics_events_log (service_name, created_at DESC);