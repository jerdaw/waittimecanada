-- 007_create_data_quality_snapshots.sql
-- Create table for caching daily data quality metrics per hospital.
-- Depends on: 002_create_tables.sql (hospitals, sources)
--
-- Quality snapshots capture scraper reliability metrics: how many
-- of the expected scrapes actually happened, gap analysis, etc.
-- These are computed daily and cached for efficient querying.

CREATE TABLE IF NOT EXISTS data_quality_snapshots (
    id BIGSERIAL PRIMARY KEY,
    hospital_id TEXT NOT NULL REFERENCES hospitals(id),
    source_id TEXT NOT NULL REFERENCES sources(id),
    snapshot_date DATE NOT NULL,

    -- Collection metrics
    expected_scrapes INTEGER NOT NULL,
    actual_scrapes INTEGER NOT NULL,
    success_rate DOUBLE PRECISION NOT NULL,
    longest_gap_minutes INTEGER,
    mean_gap_minutes DOUBLE PRECISION,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (hospital_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_quality_hospital_date
    ON data_quality_snapshots (hospital_id, snapshot_date DESC);

CREATE INDEX IF NOT EXISTS idx_quality_source_date
    ON data_quality_snapshots (source_id, snapshot_date DESC);

-- Rollback:
-- DROP TABLE IF EXISTS data_quality_snapshots;
