-- 006_create_measurement_aggregates.sql
-- Create table for permanent statistical summaries of wait time data.
-- Depends on: 002_create_tables.sql (hospitals, sources)
--
-- These aggregates keep longitudinal research and long-range trend analysis
-- efficient even when raw measurements are retained indefinitely.
-- Ontology tags are denormalized: if a source changes methodology,
-- historical aggregates preserve what the methodology was at that time.

CREATE TABLE IF NOT EXISTS measurement_aggregates (
    id BIGSERIAL PRIMARY KEY,
    hospital_id TEXT NOT NULL REFERENCES hospitals(id),
    source_id TEXT NOT NULL REFERENCES sources(id),

    -- Time period
    period_type TEXT NOT NULL CHECK (period_type IN ('hourly', 'daily', 'weekly', 'monthly')),
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,

    -- Summary statistics
    mean_value DOUBLE PRECISION NOT NULL,
    median_value DOUBLE PRECISION,
    p90_value DOUBLE PRECISION,
    min_value DOUBLE PRECISION NOT NULL,
    max_value DOUBLE PRECISION NOT NULL,
    std_dev DOUBLE PRECISION,
    sample_count INTEGER NOT NULL CHECK (sample_count > 0),

    -- Ontology snapshot (denormalized from source at aggregation time)
    metric_family TEXT NOT NULL,
    start_event TEXT NOT NULL,
    end_event TEXT NOT NULL,
    statistic_type TEXT NOT NULL,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent duplicate aggregates for the same hospital + period
    UNIQUE (hospital_id, period_type, period_start),

    -- Sanity check: period_end must be after period_start
    CONSTRAINT aggregates_period_order CHECK (period_end > period_start)
);

-- Primary query pattern: get aggregates for a hospital by period type, ordered by time
CREATE INDEX IF NOT EXISTS idx_aggregates_hospital_period
    ON measurement_aggregates (hospital_id, period_type, period_start DESC);

-- Province-level analytics: query all aggregates for a period type in time range
CREATE INDEX IF NOT EXISTS idx_aggregates_period_type_start
    ON measurement_aggregates (period_type, period_start DESC);

-- Source-level queries (e.g., data quality per source)
CREATE INDEX IF NOT EXISTS idx_aggregates_source
    ON measurement_aggregates (source_id, period_type, period_start DESC);

-- Rollback:
-- DROP TABLE IF EXISTS measurement_aggregates;
