-- 009_create_methodology_change_events.sql
-- Create table for tracking detected methodology changes.
-- Depends on: 002_create_tables.sql (sources)
--
-- When a province silently changes how they calculate wait times,
-- the system detects the distributional shift and logs it here.
-- These events are reviewed manually and either confirmed or dismissed.

CREATE TABLE IF NOT EXISTS methodology_change_events (
    id BIGSERIAL PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id),
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    previous_period_start DATE NOT NULL,
    previous_period_end DATE NOT NULL,
    current_period_start DATE NOT NULL,
    current_period_end DATE NOT NULL,
    previous_mean DOUBLE PRECISION NOT NULL,
    current_mean DOUBLE PRECISION NOT NULL,
    shift_percent DOUBLE PRECISION NOT NULL,
    hospitals_analyzed INTEGER NOT NULL,
    explanation TEXT NOT NULL,
    is_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    resolution_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_methodology_changes_source
    ON methodology_change_events (source_id, detected_at DESC);

-- Rollback:
-- DROP TABLE IF EXISTS methodology_change_events;
