-- 002_create_tables.sql
-- Create core tables for WaitTime Canada
-- Depends on: 001_create_enums.sql

-- Provincial data sources with provenance tracking
CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    province CHAR(2) NOT NULL,
    url TEXT NOT NULL,
    methodology_url TEXT,

    -- Telehealth routing info
    telehealth_name TEXT NOT NULL,
    telehealth_number TEXT NOT NULL DEFAULT '811',

    -- Default ontology for this source (scrapers can override)
    default_metric_family metric_family_enum NOT NULL,
    default_start_event start_event_enum NOT NULL,
    default_end_event end_event_enum NOT NULL,
    default_statistic_type statistic_type_enum NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Healthcare facilities that report wait times
CREATE TABLE hospitals (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    province CHAR(2) NOT NULL,
    city TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,

    -- Verification workflow - never auto-publish
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_visible BOOLEAN NOT NULL DEFAULT FALSE,

    source_id TEXT NOT NULL REFERENCES sources(id),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraint: must be verified before visible
    CONSTRAINT hospital_verify_before_visible
        CHECK (NOT (is_visible AND NOT is_verified))
);

-- Individual wait time measurements with full ontology tagging
CREATE TABLE measurements (
    id BIGSERIAL PRIMARY KEY,
    hospital_id TEXT NOT NULL REFERENCES hospitals(id),
    timestamp_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    value DOUBLE PRECISION NOT NULL CHECK (value > 0),

    -- Ontology fields (required for comparability analysis)
    metric_family metric_family_enum NOT NULL,
    start_event start_event_enum NOT NULL,
    end_event end_event_enum NOT NULL,
    statistic_type statistic_type_enum NOT NULL,
    patient_scope patient_scope_enum NOT NULL DEFAULT 'ALL',

    -- Provenance tracking
    source_id TEXT NOT NULL REFERENCES sources(id),
    raw_payload_hash CHAR(64) NOT NULL,
    raw_payload_snippet TEXT,
    parser_version TEXT NOT NULL DEFAULT 'v1.0',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Heartbeat records for monitoring scraper health
CREATE TABLE scraper_status (
    source_id TEXT PRIMARY KEY REFERENCES sources(id),
    last_run TIMESTAMPTZ NOT NULL,
    status scraper_status_enum NOT NULL DEFAULT 'healthy',
    error_message TEXT,
    measurements_count INTEGER NOT NULL DEFAULT 0,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_measurements_hospital_time
    ON measurements(hospital_id, timestamp_utc DESC);

CREATE INDEX idx_measurements_source_time
    ON measurements(source_id, timestamp_utc DESC);

CREATE INDEX idx_hospitals_province
    ON hospitals(province) WHERE is_visible = true;

CREATE INDEX idx_hospitals_source
    ON hospitals(source_id);

-- Rollback:
-- DROP TABLE IF EXISTS scraper_status;
-- DROP TABLE IF EXISTS measurements;
-- DROP TABLE IF EXISTS hospitals;
-- DROP TABLE IF EXISTS sources;
