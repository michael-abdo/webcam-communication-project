-- Analytics Database Schema for Metrics Storage
-- Designed for PostgreSQL with time-series optimization

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "timescaledb" CASCADE; -- Optional but recommended

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

-- Convert to TimescaleDB hypertable if extension is available
-- This provides automatic time-based partitioning
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        PERFORM create_hypertable('analytics_metrics', 'timestamp', 
            chunk_time_interval => interval '1 day',
            if_not_exists => TRUE
        );
    END IF;
END
$$;

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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicate aggregations
    CONSTRAINT unique_aggregate UNIQUE (
        session_id, 
        COALESCE(participant_id, '00000000-0000-0000-0000-000000000000'), 
        metric_name, 
        aggregation_type, 
        time_window, 
        window_start
    )
);

-- Create indexes for analytics_aggregates
CREATE INDEX IF NOT EXISTS idx_aggregates_session_window ON analytics_aggregates (session_id, window_start DESC);
CREATE INDEX IF NOT EXISTS idx_aggregates_metric_type ON analytics_aggregates (metric_name, aggregation_type);

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
    ttl TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '1 hour',
    
    -- Unique per session/participant
    CONSTRAINT unique_snapshot UNIQUE (
        session_id, 
        COALESCE(participant_id, '00000000-0000-0000-0000-000000000000')
    )
);

-- Create indexes for analytics_realtime_snapshots
CREATE INDEX IF NOT EXISTS idx_snapshots_session ON analytics_realtime_snapshots (session_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_ttl ON analytics_realtime_snapshots (ttl);

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

-- Materialized view for common queries (refresh periodically)
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics_session_overview AS
SELECT 
    s.session_id,
    s.participant_count,
    s.total_duration_seconds,
    s.engagement_score,
    COUNT(DISTINCT m.participant_id) as active_participants,
    COUNT(DISTINCT CASE WHEN m.metric_name = 'talk_time_seconds' THEN m.participant_id END) as speakers_count,
    MAX(m.timestamp) as last_activity
FROM analytics_session_summary s
LEFT JOIN analytics_metrics m ON s.session_id = m.session_id
GROUP BY s.session_id, s.participant_count, s.total_duration_seconds, s.engagement_score;

-- Create indexes on the materialized view
CREATE INDEX idx_mv_session_overview_session ON analytics_session_overview(session_id);
CREATE INDEX idx_mv_session_overview_last_activity ON analytics_session_overview(last_activity DESC);

-- Functions for common operations

-- Function to get participant metrics
CREATE OR REPLACE FUNCTION get_participant_metrics(
    p_session_id CHAR(36),
    p_participant_id CHAR(36),
    p_metric_names TEXT[] DEFAULT NULL
)
RETURNS TABLE (
    metric_name VARCHAR(100),
    latest_value DOUBLE PRECISION,
    total_value DOUBLE PRECISION,
    avg_value DOUBLE PRECISION,
    sample_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.metric_name,
        (SELECT metric_value FROM analytics_metrics 
         WHERE session_id = p_session_id 
         AND participant_id = p_participant_id 
         AND metric_name = m.metric_name 
         ORDER BY timestamp DESC LIMIT 1) as latest_value,
        SUM(m.metric_value) as total_value,
        AVG(m.metric_value) as avg_value,
        COUNT(*) as sample_count
    FROM analytics_metrics m
    WHERE m.session_id = p_session_id 
    AND m.participant_id = p_participant_id
    AND (p_metric_names IS NULL OR m.metric_name = ANY(p_metric_names))
    GROUP BY m.metric_name;
END;
$$ LANGUAGE plpgsql;

-- Function to compute session analytics
CREATE OR REPLACE FUNCTION compute_session_analytics(p_session_id CHAR(36))
RETURNS VOID AS $$
DECLARE
    v_participant_count INTEGER;
    v_talk_time_dist JSONB;
    v_total_talk_time DOUBLE PRECISION;
    v_total_words INTEGER;
    v_interruptions INTEGER;
BEGIN
    -- Get participant count
    SELECT COUNT(DISTINCT participant_id) INTO v_participant_count
    FROM analytics_metrics
    WHERE session_id = p_session_id AND participant_id IS NOT NULL;
    
    -- Get talk time distribution
    SELECT jsonb_object_agg(participant_id, total_seconds)
    INTO v_talk_time_dist
    FROM (
        SELECT participant_id, SUM(metric_value) as total_seconds
        FROM analytics_metrics
        WHERE session_id = p_session_id 
        AND metric_name = 'talk_time_seconds'
        AND participant_id IS NOT NULL
        GROUP BY participant_id
    ) t;
    
    -- Calculate totals
    SELECT 
        COALESCE(SUM((value->>'value')::DOUBLE PRECISION), 0),
        COALESCE(SUM(CASE WHEN key = 'words_spoken' THEN (value->>'value')::INTEGER END), 0),
        COALESCE(SUM(CASE WHEN key = 'interruption_count' THEN (value->>'value')::INTEGER END), 0)
    INTO v_total_talk_time, v_total_words, v_interruptions
    FROM analytics_metrics,
    LATERAL jsonb_each(tags) AS kv(key, value)
    WHERE session_id = p_session_id;
    
    -- Upsert session summary
    INSERT INTO analytics_session_summary (
        session_id,
        participant_count,
        talk_time_distribution,
        total_talk_time_seconds,
        total_words_spoken,
        interruption_count,
        computed_at
    ) VALUES (
        p_session_id,
        v_participant_count,
        v_talk_time_dist,
        v_total_talk_time,
        v_total_words,
        v_interruptions,
        NOW()
    )
    ON CONFLICT (session_id) DO UPDATE SET
        participant_count = EXCLUDED.participant_count,
        talk_time_distribution = EXCLUDED.talk_time_distribution,
        total_talk_time_seconds = EXCLUDED.total_talk_time_seconds,
        total_words_spoken = EXCLUDED.total_words_spoken,
        interruption_count = EXCLUDED.interruption_count,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Cleanup old data (run periodically)
CREATE OR REPLACE FUNCTION cleanup_old_analytics(days_to_keep INTEGER DEFAULT 90)
RETURNS TABLE(deleted_metrics BIGINT, deleted_aggregates BIGINT, deleted_events BIGINT) AS $$
DECLARE
    v_cutoff_date TIMESTAMPTZ;
    v_deleted_metrics BIGINT;
    v_deleted_aggregates BIGINT;
    v_deleted_events BIGINT;
BEGIN
    v_cutoff_date := NOW() - (days_to_keep || ' days')::INTERVAL;
    
    -- Delete old metrics
    WITH deleted AS (
        DELETE FROM analytics_metrics 
        WHERE timestamp < v_cutoff_date
        RETURNING 1
    )
    SELECT COUNT(*) INTO v_deleted_metrics FROM deleted;
    
    -- Delete old aggregates
    WITH deleted AS (
        DELETE FROM analytics_aggregates 
        WHERE window_end < v_cutoff_date
        RETURNING 1
    )
    SELECT COUNT(*) INTO v_deleted_aggregates FROM deleted;
    
    -- Delete old events
    WITH deleted AS (
        DELETE FROM analytics_events_log 
        WHERE created_at < v_cutoff_date
        RETURNING 1
    )
    SELECT COUNT(*) INTO v_deleted_events FROM deleted;
    
    -- Clean expired snapshots
    DELETE FROM analytics_realtime_snapshots WHERE ttl < NOW();
    
    RETURN QUERY SELECT v_deleted_metrics, v_deleted_aggregates, v_deleted_events;
END;
$$ LANGUAGE plpgsql;